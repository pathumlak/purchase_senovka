import calendar
from datetime import date as _date
from decimal import Decimal

from django.db.models import Case, DecimalField, Sum, Value, When
from django.http import HttpResponse
from django.contrib import messages
from django.template.loader import get_template
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CashSaleForm
from .models import CashSale
from erp.utils import log_activity


def _get_month_year(request):
    today = timezone.localdate()
    try:
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        month = today.month
    try:
        year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        year = today.year
    if not (1 <= month <= 12):
        month = today.month
    if not (2000 <= year <= 2100):
        year = today.year
    return month, year


def _adjacent_month(month, year, delta):
    m = month + delta
    if m < 1:
        return 12, year - 1
    if m > 12:
        return 1, year + 1
    return m, year


def _build_ledger(month, year):
    """
    Compute opening balance (all history before this month),
    per-row running balance, and closing balance.
    """
    month_start = _date(year, month, 1)

    prev = CashSale.objects.filter(date__lt=month_start).aggregate(
        total_in=Sum(
            Case(When(sale_type=CashSale.CASH_IN, then='amount'),
                 default=Value(0), output_field=DecimalField())
        ),
        total_out=Sum(
            Case(When(sale_type=CashSale.CASH_OUT, then='amount'),
                 default=Value(0), output_field=DecimalField())
        ),
    )
    opening = (prev['total_in'] or Decimal('0')) - (prev['total_out'] or Decimal('0'))

    qs = CashSale.objects.filter(
        date__year=year, date__month=month
    ).order_by('date', 'id')

    running = opening
    rows = []
    monthly_in = Decimal('0')
    monthly_out = Decimal('0')

    for entry in qs:
        if entry.sale_type == CashSale.CASH_IN:
            running += entry.amount
            monthly_in += entry.amount
        else:
            running -= entry.amount
            monthly_out += entry.amount
        rows.append({'entry': entry, 'running_balance': running})

    return {
        'opening_balance': opening,
        'ledger_rows': rows,
        'monthly_in': monthly_in,
        'monthly_out': monthly_out,
        'closing_balance': running,
    }


def sale_list(request):
    month, year = _get_month_year(request)
    prev_month, prev_year = _adjacent_month(month, year, -1)
    next_month, next_year = _adjacent_month(month, year, +1)
    today = timezone.localdate()

    ledger = _build_ledger(month, year)

    context = {
        'month': month,
        'year': year,
        'month_label': f"{calendar.month_name[month]} {year}",
        'prev_month': prev_month,
        'prev_year': prev_year,
        'prev_month_label': f"{calendar.month_name[prev_month]} {prev_year}",
        'next_month': next_month,
        'next_year': next_year,
        'next_month_label': f"{calendar.month_name[next_month]} {next_year}",
        'is_current_month': (month == today.month and year == today.year),
        **ledger,
    }
    return render(request, 'cashsales/sale_list.html', context)


def sale_create(request):
    preset_type = request.GET.get('type', '')
    if request.method == 'POST':
        form = CashSaleForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save()
            label = 'Reimbursement' if entry.sale_type == CashSale.CASH_IN else 'Payment'
            sign = '+' if entry.sale_type == CashSale.CASH_IN else '-'
            log_activity(
                request, 'pettycash', 'cash_entry_created',
                f"Petty cash {entry.get_sale_type_display()}: {entry.purpose} | {sign}Rs. {entry.amount} | {entry.date}",
                reverse('pettycash:sale_list'),
                related_id=entry.pk,
            )
            messages.success(request, f'{label} recorded successfully.')
            return redirect(
                f"{reverse('pettycash:sale_list')}?month={entry.date.month}&year={entry.date.year}"
            )
        messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        if preset_type in (CashSale.CASH_IN, CashSale.CASH_OUT):
            initial['sale_type'] = preset_type
        form = CashSaleForm(initial=initial)

    return render(request, 'cashsales/sale_form.html', {
        'form': form,
        'is_create': True,
        'preset_type': preset_type,
    })


def sale_detail(request, pk):
    record = get_object_or_404(CashSale, pk=pk)
    return render(request, 'cashsales/sale_detail.html', {'record': record})


def sale_update(request, pk):
    record = get_object_or_404(CashSale, pk=pk)
    if request.method == 'POST':
        form = CashSaleForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            entry = form.save()
            messages.success(request, 'Entry updated successfully.')
            return redirect(
                f"{reverse('pettycash:sale_list')}?month={entry.date.month}&year={entry.date.year}"
            )
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CashSaleForm(instance=record)

    return render(request, 'cashsales/sale_form.html', {
        'form': form,
        'record': record,
        'is_create': False,
        'preset_type': record.sale_type,
    })


def sale_delete(request, pk):
    record = get_object_or_404(CashSale, pk=pk)
    if request.method == 'POST':
        month, year = record.date.month, record.date.year
        desc = f"Petty cash deleted: {record.purpose} | Rs. {record.amount} | {record.date}"
        record.delete()
        log_activity(request, 'pettycash', 'cash_entry_deleted', desc, reverse('pettycash:sale_list'))
        messages.success(request, 'Entry deleted.')
        return redirect(f"{reverse('pettycash:sale_list')}?month={month}&year={year}")
    return render(request, 'cashsales/sale_confirm_delete.html', {'record': record})


# ── Exports ───────────────────────────────────────────────────────────────────

def monthly_export_excel(request):
    month, year = _get_month_year(request)
    month_label = f"{calendar.month_name[month]} {year}"
    ledger = _build_ledger(month, year)

    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse('Excel export dependency missing: openpyxl', status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Petty Cash Ledger'

    generated_at = timezone.localtime()
    ws.append(['Petty Cash Ledger — SENOVKA ERP'])
    ws.append(['Period', month_label])
    ws.append(['Generated At', generated_at.strftime('%d %b %Y %I:%M %p')])
    ws.append([])
    ws.append(['Opening Balance', float(ledger['opening_balance'])])
    ws.append(['Total Reimbursements (+)', float(ledger['monthly_in'])])
    ws.append(['Total Payments (-)', float(ledger['monthly_out'])])
    ws.append(['Closing Balance', float(ledger['closing_balance'])])
    ws.append([])
    ws.append(['Date', 'Description', 'Reference', 'Reimbursement (In)', 'Payment (Out)', 'Balance'])
    ws.append(['', 'Opening Balance (brought forward)', '', '', '', float(ledger['opening_balance'])])

    for row in ledger['ledger_rows']:
        e = row['entry']
        ws.append([
            e.date.strftime('%d-%m-%Y'),
            e.purpose,
            e.reference_number or '',
            float(e.amount) if e.sale_type == CashSale.CASH_IN else '',
            float(e.amount) if e.sale_type == CashSale.CASH_OUT else '',
            float(row['running_balance']),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="pettycash_{year}_{month:02d}.xlsx"'
    wb.save(response)
    return response


def monthly_export_pdf(request):
    month, year = _get_month_year(request)
    month_label = f"{calendar.month_name[month]} {year}"
    ledger = _build_ledger(month, year)

    context = {
        'month_label': month_label,
        'generated_at': timezone.localtime(),
        **ledger,
    }

    template = get_template('cashsales/monthly_pettycash_pdf.html')
    html = template.render(context)

    try:
        from xhtml2pdf import pisa
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="pettycash_{year}_{month:02d}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('PDF generation error', status=500)
        return response
    except ImportError:
        context['printable'] = True
        return render(request, 'cashsales/monthly_pettycash_pdf.html', context)
