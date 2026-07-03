import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from .models import Supplier, SupplyReceipt, SupplyReceiptItem, PurchaseOrder, PurchaseOrderItem
from apps.production.models import Product, ProductCategory
from apps.customers.models import Customer, CustomerLedger, add_ledger_entry
from erp.utils import resolve_date_range


# ── Supplier CRUD ──────────────────────────────────────────────────────────────

@login_required
def supplier_list(request):
    q = request.GET.get('q', '').strip()
    date_from, date_to = resolve_date_range(request)
    qs = Supplier.objects.select_related('customer').prefetch_related('receipts').all()
    if q:
        qs = qs.filter(name__icontains=q)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'suppliers/supplier_list.html', {
        'page_obj': page_obj, 'q': q, 'date_from': date_from, 'date_to': date_to,
    })


@login_required
def supplier_create(request):
    available_customers = Customer.objects.filter(as_supplier__isnull=True).order_by('name')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Supplier name is required.')
            return render(request, 'suppliers/supplier_form.html', {
                'available_customers': available_customers, 'action': 'Create', 'name_value': name,
            })
        if Supplier.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A supplier named "{name}" already exists.')
            return render(request, 'suppliers/supplier_form.html', {
                'available_customers': available_customers, 'action': 'Create', 'name_value': name,
            })

        customer_id = request.POST.get('customer_id') or None
        customer = get_object_or_404(Customer, pk=customer_id) if customer_id else None

        supplier = Supplier.objects.create(
            name=name,
            phone=request.POST.get('phone', '').strip(),
            email=request.POST.get('email', '').strip(),
            address=request.POST.get('address', '').strip(),
            notes=request.POST.get('notes', '').strip(),
            customer=customer,
        )
        messages.success(request, f'Supplier "{supplier.name}" created.')
        return redirect('suppliers:supplier_detail', pk=supplier.pk)

    return render(request, 'suppliers/supplier_form.html', {
        'available_customers': available_customers, 'action': 'Create', 'name_value': '',
    })


@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    qs = Customer.objects.filter(as_supplier__isnull=True)
    if supplier.customer:
        qs = (qs | Customer.objects.filter(pk=supplier.customer.pk)).distinct()
    available_customers = qs.order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Supplier name is required.')
            return render(request, 'suppliers/supplier_form.html', {
                'supplier': supplier, 'available_customers': available_customers, 'action': 'Edit', 'name_value': name,
            })
        if Supplier.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Another supplier named "{name}" already exists.')
            return render(request, 'suppliers/supplier_form.html', {
                'supplier': supplier, 'available_customers': available_customers, 'action': 'Edit', 'name_value': name,
            })

        customer_id = request.POST.get('customer_id') or None
        customer = get_object_or_404(Customer, pk=customer_id) if customer_id else None

        supplier.name    = name
        supplier.phone   = request.POST.get('phone', '').strip()
        supplier.email   = request.POST.get('email', '').strip()
        supplier.address = request.POST.get('address', '').strip()
        supplier.notes   = request.POST.get('notes', '').strip()
        supplier.customer = customer
        supplier.save()

        messages.success(request, f'Supplier "{supplier.name}" updated.')
        return redirect('suppliers:supplier_detail', pk=supplier.pk)

    return render(request, 'suppliers/supplier_form.html', {
        'supplier': supplier, 'available_customers': available_customers, 'action': 'Edit', 'name_value': supplier.name,
    })


@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        name = supplier.name
        supplier.delete()
        messages.success(request, f'Supplier "{name}" deleted.')
        return redirect('suppliers:supplier_list')
    return render(request, 'suppliers/supplier_delete.html', {'supplier': supplier})


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier.objects.select_related('customer'), pk=pk)
    receipts = supplier.receipts.prefetch_related('items__product__category').all()
    products = Product.objects.filter(supplier=supplier).select_related('category').order_by('name')
    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'receipts': receipts,
        'products': products,
    })


# ── Supply Record ──────────────────────────────────────────────────────────────

@login_required
def supply_record(request):
    suppliers  = Supplier.objects.select_related('customer').order_by('name')
    categories = ProductCategory.objects.order_by('name')
    selected_supplier_id = request.GET.get('supplier', '')

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id', '').strip()
        supply_date = request.POST.get('supply_date', '').strip()
        notes       = request.POST.get('notes', '').strip()
        items_raw   = request.POST.get('items_json', '[]')

        ctx = {'suppliers': suppliers, 'categories': categories, 'today': timezone.localdate()}

        if not supplier_id:
            messages.error(request, 'Please select a supplier.')
            return render(request, 'suppliers/supply_record.html', ctx)

        try:
            items = json.loads(items_raw)
        except (json.JSONDecodeError, ValueError):
            messages.error(request, 'Invalid items data.')
            return render(request, 'suppliers/supply_record.html', ctx)

        if not items:
            messages.error(request, 'Please add at least one product.')
            return render(request, 'suppliers/supply_record.html', ctx)

        supplier = get_object_or_404(Supplier.objects.select_related('customer'), pk=supplier_id)

        with transaction.atomic():
            total_cost  = Decimal('0')
            saved_items = []

            for item in items:
                try:
                    qty  = Decimal(str(item.get('qty', 0)))
                    cost = Decimal(str(item.get('cost_price', 0)))
                except InvalidOperation:
                    continue
                if qty <= 0:
                    continue

                product_id = item.get('product_id')

                if product_id:
                    product = get_object_or_404(Product, pk=product_id)
                else:
                    cat_id = item.get('category_id')
                    pname  = (item.get('product_name') or '').strip()
                    if not cat_id or not pname:
                        continue
                    category = get_object_or_404(ProductCategory, pk=cat_id)
                    product, _ = Product.objects.get_or_create(
                        name=pname,
                        category=category,
                        defaults={
                            'size': (item.get('size') or '').strip() or None,
                            'qty': Decimal('0'),
                            'supplier': supplier,
                        },
                    )

                if not product.supplier_id:
                    product.supplier = supplier
                    product.save(update_fields=['supplier'])

                product.qty = (product.qty or Decimal('0')) + qty
                product.save(update_fields=['qty'])

                line_total = qty * cost
                total_cost += line_total
                saved_items.append({
                    'product':    product,
                    'quantity':   qty,
                    'cost_price': cost,
                    'line_total': line_total,
                })

            if not saved_items:
                messages.error(request, 'No valid products were added.')
                return render(request, 'suppliers/supply_record.html', ctx)

            receipt = SupplyReceipt.objects.create(
                supplier=supplier,
                date=supply_date or timezone.localdate(),
                notes=notes,
                total_cost=total_cost,
                credit_applied=bool(supplier.customer),
            )
            for si in saved_items:
                SupplyReceiptItem.objects.create(
                    receipt=receipt,
                    product=si['product'],
                    quantity=si['quantity'],
                    cost_price=si['cost_price'],
                    line_total=si['line_total'],
                )

            if supplier.customer:
                customer = supplier.customer
                customer.balance = (customer.balance or Decimal('0')) + total_cost
                customer.save(update_fields=['balance'])
                add_ledger_entry(
                    customer=customer,
                    date=receipt.date,
                    description=f"Supply received — {supplier.name} (Supply #{receipt.pk})",
                    transaction_type=CustomerLedger.SUPPLY_CREDIT,
                    debit=Decimal('0'),
                    credit=total_cost,
                    balance=customer.balance,
                )

        credit_msg = f' — Rs. {total_cost:,.2f} credited to {supplier.customer.name}.' if supplier.customer else '.'
        messages.success(request, f'Supply recorded: {len(saved_items)} product(s){credit_msg}')
        return redirect('suppliers:supply_detail', pk=receipt.pk)

    return render(request, 'suppliers/supply_record.html', {
        'suppliers': suppliers,
        'categories': categories,
        'today': timezone.localdate(),
        'selected_supplier_id': selected_supplier_id,
    })


@login_required
def supply_detail(request, pk):
    receipt = get_object_or_404(
        SupplyReceipt.objects.select_related('supplier__customer')
                             .prefetch_related('items__product__category'),
        pk=pk,
    )
    return render(request, 'suppliers/supply_detail.html', {'receipt': receipt})


@login_required
def supply_delete(request, pk):
    receipt = get_object_or_404(
        SupplyReceipt.objects.select_related('supplier__customer'),
        pk=pk,
    )
    if request.method == 'POST':
        supplier = receipt.supplier
        with transaction.atomic():
            for item in receipt.items.select_related('product').all():
                item.product.qty = max(Decimal('0'), item.product.qty - item.quantity)
                item.product.save(update_fields=['qty'])

            if receipt.credit_applied and supplier.customer:
                customer = supplier.customer
                old_balance = customer.balance or Decimal('0')
                customer.balance = max(Decimal('0'), old_balance - receipt.total_cost)
                customer.save(update_fields=['balance'])
                add_ledger_entry(
                    customer=customer,
                    date=timezone.localdate(),
                    description=f"Supply reversed — {supplier.name} (Supply #{receipt.pk})",
                    transaction_type=CustomerLedger.SUPPLY_CREDIT_REVERSAL,
                    debit=old_balance - customer.balance,
                    credit=Decimal('0'),
                    balance=customer.balance,
                )

            receipt.delete()

        messages.success(request, 'Supply receipt deleted and stock reversed.')
        return redirect('suppliers:supplier_detail', pk=supplier.pk)

    return render(request, 'suppliers/supply_delete.html', {'receipt': receipt})


# ── API ────────────────────────────────────────────────────────────────────────

@login_required
def api_product_search(request):
    q  = request.GET.get('q', '').strip()
    qs = Product.objects.select_related('category').order_by('name')
    if q:
        qs = qs.filter(name__icontains=q)
    results = [
        {
            'id':          p.id,
            'name':        p.name,
            'category':    p.category.name,
            'category_id': p.category.id,
            'size':        p.size or '',
            'qty':         float(p.qty),
        }
        for p in qs[:20]
    ]
    return JsonResponse({'results': results})


# ── Purchase Orders ────────────────────────────────────────────────────────────

@login_required
def purchase_order_list(request):
    status_filter   = request.GET.get('status', '').strip()
    supplier_filter = request.GET.get('supplier', '').strip()
    qs = PurchaseOrder.objects.select_related('supplier').prefetch_related('items')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if supplier_filter and supplier_filter.isdigit():
        qs = qs.filter(supplier_id=supplier_filter)
    suppliers = Supplier.objects.order_by('name')
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'suppliers/purchase_order_list.html', {
        'page_obj': page_obj,
        'suppliers': suppliers,
        'status_filter': status_filter,
        'supplier_filter': supplier_filter,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
    })


@login_required
def purchase_order_create(request):
    suppliers  = Supplier.objects.select_related('customer').order_by('name')
    products   = Product.objects.select_related('category').order_by('name')
    today      = timezone.localdate()

    if request.method == 'POST':
        supplier_id   = request.POST.get('supplier_id', '').strip()
        order_date    = request.POST.get('order_date', str(today)).strip()
        expected_date = request.POST.get('expected_date', '').strip() or None
        notes         = request.POST.get('notes', '').strip()
        items_raw     = request.POST.get('items_json', '[]')

        ctx = {'suppliers': suppliers, 'products': products, 'today': today}

        if not supplier_id:
            messages.error(request, 'Please select a supplier.')
            return render(request, 'suppliers/purchase_order_form.html', ctx)

        try:
            items = json.loads(items_raw)
        except (json.JSONDecodeError, ValueError):
            messages.error(request, 'Invalid items data.')
            return render(request, 'suppliers/purchase_order_form.html', ctx)

        if not items:
            messages.error(request, 'Please add at least one item.')
            return render(request, 'suppliers/purchase_order_form.html', ctx)

        supplier = get_object_or_404(Supplier.objects.select_related('customer'), pk=supplier_id)

        with transaction.atomic():
            total_cost  = Decimal('0')
            saved_items = []

            for item in items:
                try:
                    qty   = Decimal(str(item.get('qty', 0)))
                    price = Decimal(str(item.get('unit_price', 0)))
                except InvalidOperation:
                    continue
                if qty <= 0:
                    continue
                product_id = item.get('product_id')
                if not product_id:
                    continue
                product = get_object_or_404(Product, pk=product_id)
                line_total  = qty * price
                total_cost += line_total
                saved_items.append({'product': product, 'qty': qty, 'price': price, 'line_total': line_total})

            if not saved_items:
                messages.error(request, 'No valid items were added.')
                return render(request, 'suppliers/purchase_order_form.html', ctx)

            order = PurchaseOrder.objects.create(
                supplier=supplier,
                order_date=order_date,
                expected_date=expected_date,
                notes=notes,
                total_cost=total_cost,
            )
            for si in saved_items:
                PurchaseOrderItem.objects.create(
                    order=order,
                    product=si['product'],
                    quantity=si['qty'],
                    unit_price=si['price'],
                    line_total=si['line_total'],
                )

        messages.success(request, f'Purchase order {order.order_number} created successfully.')
        return redirect('suppliers:purchase_order_detail', pk=order.pk)

    return render(request, 'suppliers/purchase_order_form.html', {
        'suppliers': suppliers, 'products': products, 'today': today,
    })


@login_required
def purchase_order_detail(request, pk):
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier__customer').prefetch_related('items__product__category'),
        pk=pk,
    )
    return render(request, 'suppliers/purchase_order_detail.html', {'order': order})


@login_required
def purchase_order_receive(request, pk):
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier__customer').prefetch_related('items__product'),
        pk=pk,
    )
    if request.method == 'POST':
        if order.status != PurchaseOrder.PENDING:
            messages.error(request, 'Only pending orders can be marked as received.')
            return redirect('suppliers:purchase_order_detail', pk=pk)

        today = timezone.localdate()
        with transaction.atomic():
            for item in order.items.all():
                item.product.qty = (item.product.qty or Decimal('0')) + item.quantity
                item.product.save(update_fields=['qty'])

            order.status        = PurchaseOrder.RECEIVED
            order.received_date = today

            if order.supplier.customer:
                customer = order.supplier.customer
                customer.balance = (customer.balance or Decimal('0')) + order.total_cost
                customer.save(update_fields=['balance'])
                order.balance_deducted = True
                add_ledger_entry(
                    customer=customer,
                    date=today,
                    description=f"Purchase received — {order.order_number} ({order.supplier.name})",
                    transaction_type=CustomerLedger.PURCHASE_OFFSET,
                    debit=Decimal('0'),
                    credit=order.total_cost,
                    balance=customer.balance,
                )

            order.save(update_fields=['status', 'received_date', 'balance_deducted'])

        msg = f'Order {order.order_number} received. Stock updated.'
        if order.balance_deducted:
            msg += f' Rs. {order.total_cost:,.2f} credited to {order.supplier.customer.name}\'s balance.'
        messages.success(request, msg)
    return redirect('suppliers:purchase_order_detail', pk=pk)


@login_required
def purchase_order_cancel(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        if order.status != PurchaseOrder.PENDING:
            messages.error(request, 'Only pending orders can be cancelled.')
        else:
            order.status = PurchaseOrder.CANCELLED
            order.save(update_fields=['status'])
            messages.success(request, f'Order {order.order_number} cancelled.')
    return redirect('suppliers:purchase_order_detail', pk=pk)


@login_required
def purchase_order_delete(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        if order.status == PurchaseOrder.RECEIVED:
            messages.error(request, 'Received orders cannot be deleted.')
            return redirect('suppliers:purchase_order_detail', pk=pk)
        num = order.order_number
        order.delete()
        messages.success(request, f'Purchase order {num} deleted.')
        return redirect('suppliers:purchase_order_list')
    return redirect('suppliers:purchase_order_detail', pk=pk)


@login_required
def purchase_order_pdf(request, pk):
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier__customer').prefetch_related('items__product__category'),
        pk=pk,
    )
    from django.template.loader import get_template
    from django.http import HttpResponse
    context = {'order': order, 'generated_at': timezone.localtime()}
    template = get_template('suppliers/purchase_order_pdf.html')
    html = template.render(context)
    try:
        from xhtml2pdf import pisa
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{order.order_number}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('PDF generation error', status=500)
        return response
    except ImportError:
        return render(request, 'suppliers/purchase_order_pdf.html', {**context, 'printable': True})


@login_required
def purchase_order_excel(request, pk):
    order = get_object_or_404(
        PurchaseOrder.objects.select_related('supplier').prefetch_related('items__product__category'),
        pk=pk,
    )
    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse('openpyxl not installed', status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = order.order_number

    ws.append(['Purchase Order', order.order_number])
    ws.append(['Supplier', order.supplier.name])
    ws.append(['Order Date', order.order_date.strftime('%d %b %Y')])
    ws.append(['Expected Date', order.expected_date.strftime('%d %b %Y') if order.expected_date else '—'])
    ws.append(['Status', order.get_status_display()])
    ws.append(['Notes', order.notes or ''])
    ws.append([])
    ws.append(['#', 'Product', 'Category', 'Qty', 'Unit Price', 'Line Total'])
    for i, item in enumerate(order.items.all(), 1):
        ws.append([
            i, item.product.name, item.product.category.name,
            float(item.quantity), float(item.unit_price), float(item.line_total),
        ])
    ws.append([])
    ws.append(['', '', '', '', 'TOTAL', float(order.total_cost)])

    from django.http import HttpResponse
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{order.order_number}.xlsx"'
    wb.save(response)
    return response
