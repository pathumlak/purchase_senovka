import datetime as _dt
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from django.db import transaction

from apps.billing.models import Bill, BillItem, Payment
from apps.booking.models import BookingOrder
from apps.customers.models import Customer
from apps.material_purchasing.models import MaterialPurchase
from apps.pettycash.models import CashSale
from apps.production.models import Product, ProductCategory, DailyRunningMachine
from apps.reminders.models import Reminder
from apps.tasks.models import Task
from django import forms as django_forms
from .decorators import superadmin_required
from .models import ActivityLog, UserProfile, CompanySettings
from .utils import resolve_date_range


class CompanySettingsForm(django_forms.ModelForm):
    class Meta:
        model  = CompanySettings
        fields = ['company_name', 'tagline', 'address', 'phone1', 'phone2', 'email', 'website']
        widgets = {
            'address': django_forms.Textarea(attrs={'rows': 3}),
        }


LOW_STOCK_THRESHOLD = Decimal('10.00')
CRITICAL_STOCK_THRESHOLD = Decimal('3.00')
RECENT_TASK_LIMIT = 5
LOW_STOCK_LIMIT = 8
ALERT_LOOKAHEAD_DAYS = 3
NOTIFICATION_SOUND_PATH = 'audio/notification.mp3'

LOG_CATEGORY_CHOICES = {
    'all': 'All Categories',
    'billing': 'Billing',
    'booking': 'Order Booking',
    'customers': 'Customers',
    'pettycash': 'Petty Cash',
    'production': 'Production',
    'purchasing': 'Purchasing',
    'users': 'User Management',
    'system': 'System',
}


def _build_recent_tasks():
    tasks = []

    recent_customers = Customer.objects.order_by('-created_at')[:8]
    for customer in recent_customers:
        tasks.append({
            'kind': 'customer',
            'title': f"New customer: {customer.name}",
            'subtitle': 'Customer profile created',
            'timestamp': customer.created_at,
            'url': reverse('customer_list'),
        })

    tasks.sort(key=lambda item: item['timestamp'], reverse=True)
    return tasks[:RECENT_TASK_LIMIT]


def _build_low_stock_rows(products):
    rows = []
    threshold_value = float(LOW_STOCK_THRESHOLD)

    for product in products:
        qty_value = float(product.qty)

        if product.qty <= 0:
            severity = 'out'
            severity_label = 'Out of stock'
        elif product.qty <= CRITICAL_STOCK_THRESHOLD:
            severity = 'critical'
            severity_label = 'Critical'
        else:
            severity = 'low'
            severity_label = 'Low'

        meter_percent = 0
        if threshold_value > 0:
            meter_percent = int(max(0, min(100, (qty_value / threshold_value) * 100)))

        rows.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else '-',
            'qty': product.qty,
            'severity': severity,
            'severity_label': severity_label,
            'meter_percent': meter_percent,
        })

    return rows


def _build_home_notifications(today):
    notifications = []
    lookahead = today + timedelta(days=ALERT_LOOKAHEAD_DAYS)

    # Low stock
    low_stock_products = list(
        Product.objects.filter(qty__lte=LOW_STOCK_THRESHOLD).order_by('qty', 'name')[:5]
    )
    if low_stock_products:
        names = ', '.join(product.name for product in low_stock_products)
        product_ids = '-'.join(str(product.id) for product in low_stock_products)
        notifications.append({
            'id': f"low-stock:{product_ids}",
            'kind': 'low_stock',
            'title': f"{len(low_stock_products)} low-stock product(s)",
            'message': names,
            'url': reverse('product_list'),
        })

    # Cheque maturity alerts
    due_cheques = list(
        Payment.objects.select_related('bill__customer')
        .filter(
            method=Payment.CHEQUE,
            cheque_status=Payment.CHQ_PENDING,
            maturity_date__gte=today,
            maturity_date__lte=lookahead,
        )
        .order_by('maturity_date')
    )
    today_cheques = [p for p in due_cheques if p.maturity_date == today]
    soon_cheques  = [p for p in due_cheques if p.maturity_date != today]

    if today_cheques:
        ids = '-'.join(str(p.id) for p in today_cheques)
        notifications.append({
            'id': f"cheque-today:{ids}",
            'kind': 'cheque_alert',
            'title': f"{len(today_cheques)} cheque(s) maturing today",
            'message': ', '.join(
                f"{p.bill.customer.name} Rs.{p.amount}" for p in today_cheques[:3]
            ),
            'url': reverse('billing:cheque_sales'),
        })
    if soon_cheques:
        ids = '-'.join(str(p.id) for p in soon_cheques)
        notifications.append({
            'id': f"cheque-soon:{ids}",
            'kind': 'cheque_alert',
            'title': f"{len(soon_cheques)} cheque(s) maturing within {ALERT_LOOKAHEAD_DAYS} days",
            'message': ', '.join(
                f"{p.bill.customer.name} Rs.{p.amount}" for p in soon_cheques[:3]
            ),
            'url': reverse('billing:cheque_sales'),
        })

    # Task due-soon alerts
    due_tasks = list(
        Task.objects.select_related('assigned_to')
        .exclude(status=Task.DONE)
        .filter(due_date__gte=today, due_date__lte=lookahead)
        .order_by('due_date', 'priority')
    )
    today_tasks = [t for t in due_tasks if t.due_date == today]
    soon_tasks  = [t for t in due_tasks if t.due_date != today]

    if today_tasks:
        ids = '-'.join(str(t.id) for t in today_tasks)
        notifications.append({
            'id': f"task-today:{ids}",
            'kind': 'task_alert',
            'title': f"{len(today_tasks)} task(s) due today",
            'message': ', '.join(t.title for t in today_tasks[:3]),
            'url': reverse('task_board'),
        })
    if soon_tasks:
        ids = '-'.join(str(t.id) for t in soon_tasks)
        notifications.append({
            'id': f"task-soon:{ids}",
            'kind': 'task_alert',
            'title': f"{len(soon_tasks)} task(s) due within {ALERT_LOOKAHEAD_DAYS} days",
            'message': ', '.join(t.title for t in soon_tasks[:3]),
            'url': reverse('task_board'),
        })

    # Overdue tasks
    overdue_tasks = list(
        Task.objects.exclude(status=Task.DONE)
        .filter(due_date__lt=today)
        .order_by('due_date')
    )
    if overdue_tasks:
        ids = '-'.join(str(t.id) for t in overdue_tasks)
        notifications.append({
            'id': f"task-overdue:{ids}",
            'kind': 'task_overdue',
            'title': f"{len(overdue_tasks)} task(s) overdue",
            'message': ', '.join(t.title for t in overdue_tasks[:3]),
            'url': reverse('task_board'),
        })

    # Pending booking order dispatch alerts
    due_bookings = list(
        BookingOrder.objects.select_related('customer')
        .filter(
            status=BookingOrder.PENDING,
            order_sending_date__gte=today,
            order_sending_date__lte=lookahead,
        )
        .order_by('order_sending_date')
    )
    today_bookings = [b for b in due_bookings if b.order_sending_date == today]
    soon_bookings  = [b for b in due_bookings if b.order_sending_date != today]

    if today_bookings:
        ids = '-'.join(str(b.id) for b in today_bookings)
        notifications.append({
            'id': f"booking-today:{ids}",
            'kind': 'booking_alert',
            'title': f"{len(today_bookings)} order(s) due for dispatch today",
            'message': ', '.join(
                f"{b.booking_number} â€“ {b.customer.name}" for b in today_bookings[:3]
            ),
            'url': reverse('booking:booking_list'),
        })
    if soon_bookings:
        ids = '-'.join(str(b.id) for b in soon_bookings)
        notifications.append({
            'id': f"booking-soon:{ids}",
            'kind': 'booking_alert',
            'title': f"{len(soon_bookings)} order(s) due within {ALERT_LOOKAHEAD_DAYS} days",
            'message': ', '.join(
                f"{b.booking_number} â€“ {b.customer.name}" for b in soon_bookings[:3]
            ),
            'url': reverse('booking:booking_list'),
        })

    # Reminders (personal reminders created in the Reminders module)
    active_reminders = list(
        Reminder.objects.filter(is_done=False, remind_date__lte=lookahead)
        .order_by('remind_date', 'remind_time')
    )
    overdue_reminders = [r for r in active_reminders if r.remind_date < today]
    today_reminders   = [r for r in active_reminders if r.remind_date == today]
    soon_reminders    = [r for r in active_reminders if r.remind_date > today]

    if overdue_reminders:
        ids = '-'.join(str(r.id) for r in overdue_reminders)
        notifications.append({
            'id': f"reminder-overdue:{ids}",
            'kind': 'reminder_overdue',
            'title': f"{len(overdue_reminders)} reminder(s) overdue",
            'message': ', '.join(r.title for r in overdue_reminders[:3]),
            'url': reverse('reminder_list'),
        })
    if today_reminders:
        ids = '-'.join(str(r.id) for r in today_reminders)
        notifications.append({
            'id': f"reminder-today:{ids}",
            'kind': 'reminder_alert',
            'title': f"{len(today_reminders)} reminder(s) due today",
            'message': ', '.join(r.title for r in today_reminders[:3]),
            'url': reverse('reminder_list'),
        })
    if soon_reminders:
        ids = '-'.join(str(r.id) for r in soon_reminders)
        notifications.append({
            'id': f"reminder-soon:{ids}",
            'kind': 'reminder_alert',
            'title': f"{len(soon_reminders)} reminder(s) within {ALERT_LOOKAHEAD_DAYS} days",
            'message': ', '.join(r.title for r in soon_reminders[:3]),
            'url': reverse('reminder_list'),
        })

    return notifications


def _build_all_logs(today):
    logs = []

    # Billing â€” bills
    for bill in Bill.objects.select_related('customer').order_by('-created_at'):
        if bill.status == Bill.CANCELLED:
            logs.append({
                'category': 'billing',
                'kind': 'bill_cancelled',
                'timestamp': bill.updated_at,
                'title': f"Bill cancelled: {bill.bill_number}",
                'message': f"{bill.customer.name} | Rs. {bill.total_amount}",
                'url': reverse('billing:bill_detail', kwargs={'pk': bill.pk}),
            })
        logs.append({
            'category': 'billing',
            'kind': 'bill_created',
            'timestamp': bill.created_at,
            'title': f"Bill created: {bill.bill_number}",
            'message': f"{bill.customer.name} | Rs. {bill.total_amount} | {bill.get_status_display()}",
            'url': reverse('billing:bill_detail', kwargs={'pk': bill.pk}),
        })

    # Billing â€” payments
    for payment in Payment.objects.select_related('bill__customer').order_by('-created_at'):
        logs.append({
            'category': 'billing',
            'kind': 'payment',
            'timestamp': payment.created_at,
            'title': f"Payment received: {payment.bill.bill_number}",
            'message': (
                f"{payment.bill.customer.name} | {payment.get_method_display()} | "
                f"Rs. {payment.amount}"
            ),
            'url': reverse('billing:bill_detail', kwargs={'pk': payment.bill_id}),
        })

    # Order booking
    for booking in BookingOrder.objects.select_related('customer').order_by('-created_at'):
        if booking.status == BookingOrder.CONFIRMED:
            logs.append({
                'category': 'booking',
                'kind': 'booking_confirmed',
                'timestamp': booking.updated_at,
                'title': f"Booking confirmed: {booking.booking_number}",
                'message': f"{booking.customer.name} | Rs. {booking.total_amount} | Converted to bill",
                'url': reverse('booking:booking_detail', kwargs={'pk': booking.pk}),
            })
        if booking.status == BookingOrder.CANCELLED:
            logs.append({
                'category': 'booking',
                'kind': 'booking_cancelled',
                'timestamp': booking.updated_at,
                'title': f"Booking cancelled: {booking.booking_number}",
                'message': f"{booking.customer.name} | Rs. {booking.total_amount}",
                'url': reverse('booking:booking_detail', kwargs={'pk': booking.pk}),
            })
        logs.append({
            'category': 'booking',
            'kind': 'booking_created',
            'timestamp': booking.created_at,
            'title': f"Booking created: {booking.booking_number}",
            'message': f"{booking.customer.name} | Rs. {booking.total_amount}",
            'url': reverse('booking:booking_detail', kwargs={'pk': booking.pk}),
        })

    # Customers
    for customer in Customer.objects.order_by('-created_at'):
        logs.append({
            'category': 'customers',
            'kind': 'customer',
            'timestamp': customer.created_at,
            'title': f"Customer created: {customer.name}",
            'message': "Customer profile added to ERP",
            'url': reverse('customer_list'),
        })

    # Petty cash
    for sale in CashSale.objects.order_by('-created_at'):
        sign = '+' if sale.sale_type == CashSale.CASH_IN else '-'
        logs.append({
            'category': 'pettycash',
            'kind': 'petty_cash',
            'timestamp': sale.created_at,
            'title': f"Petty cash entry: {sale.get_sale_type_display()}",
            'message': (
                f"{sale.date} | {sale.purpose} | "
                f"{sign}{sale.amount}"
            ),
            'url': reverse('pettycash:sale_detail', kwargs={'pk': sale.pk}),
        })

    # Production â€” categories
    for category in ProductCategory.objects.order_by('-created_at'):
        logs.append({
            'category': 'production',
            'kind': 'category',
            'timestamp': category.created_at,
            'title': f"Category created: {category.name}",
            'message': "Product category added",
            'url': reverse('category_list'),
        })

    # Production â€” products
    for product in Product.objects.select_related('category').order_by('-created_at'):
        logs.append({
            'category': 'production',
            'kind': 'product',
            'timestamp': product.created_at,
            'title': f"Product added: {product.name}",
            'message': f"Category {product.category.name} | Opening qty {product.qty}",
            'url': reverse('product_list'),
        })

    # Purchasing â€” material purchases
    for purchase in MaterialPurchase.objects.order_by('-created_at'):
        logs.append({
            'category': 'purchasing',
            'kind': 'purchase',
            'timestamp': purchase.created_at,
            'title': f"Material purchased: {purchase.material_name}",
            'message': (
                f"Supplier: {purchase.supplier_name} | Invoice: {purchase.invoice_number} | "
                f"Rs. {purchase.total_amount}"
            ),
            'url': reverse('purchasing:purchase_list'),
        })

    # Alerts â€” low stock
    low_stock_products = list(
        Product.objects.filter(qty__lte=LOW_STOCK_THRESHOLD).order_by('qty', 'name')
    )
    if low_stock_products:
        names = ', '.join(product.name for product in low_stock_products[:5])
        low_stock_activity_at = max(product.updated_at for product in low_stock_products)
        logs.append({
            'category': 'alerts',
            'kind': 'low_stock',
            'timestamp': low_stock_activity_at,
            'title': f"Low stock alert: {len(low_stock_products)} product(s)",
            'message': names,
            'url': reverse('product_list'),
        })

    logs.sort(key=lambda item: item['timestamp'], reverse=True)
    return logs


def _selected_log_category(request):
    requested = request.GET.get('category', 'all')
    if requested in LOG_CATEGORY_CHOICES:
        return requested
    return 'all'


def _filter_logs_by_category(logs, selected_category):
    if selected_category == 'all':
        return logs
    return [log for log in logs if log['category'] == selected_category]


def _logs_context_payload(request):
    today = timezone.localdate()
    all_logs_list = _build_all_logs(today)
    selected_category = _selected_log_category(request)
    filtered_logs = _filter_logs_by_category(all_logs_list, selected_category)

    return {
        'all_logs_list': all_logs_list,
        'filtered_logs': filtered_logs,
        'selected_category': selected_category,
        'selected_category_label': LOG_CATEGORY_CHOICES[selected_category],
        'log_categories': LOG_CATEGORY_CHOICES,
    }


def home(request):
    if not request.user.is_authenticated:
        return render(request, 'landing.html')
    today = timezone.localdate()
    current_month_start = today.replace(day=1)

    total_products = Product.objects.count()
    total_customers = Customer.objects.count()
    new_customers_today = Customer.objects.filter(created_at__date=today).count()

    petty_cash_month_qs = CashSale.objects.filter(date__year=today.year, date__month=today.month)
    petty_cash_month_in = petty_cash_month_qs.filter(sale_type=CashSale.CASH_IN).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    petty_cash_month_out = petty_cash_month_qs.filter(sale_type=CashSale.CASH_OUT).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    petty_cash_month_net = petty_cash_month_in - petty_cash_month_out

    low_stock_queryset = (
        Product.objects
        .select_related('category')
        .filter(qty__lte=LOW_STOCK_THRESHOLD)
        .order_by('qty', 'name')
    )
    low_stock_count = low_stock_queryset.count()
    out_of_stock_count = Product.objects.filter(qty__lte=0).count()
    critical_stock_count = Product.objects.filter(
        qty__gt=0,
        qty__lte=CRITICAL_STOCK_THRESHOLD,
    ).count()

    recent_tasks = _build_recent_tasks()
    low_stock_items = _build_low_stock_rows(low_stock_queryset[:LOW_STOCK_LIMIT])
    home_notifications = _build_home_notifications(today)

    cheque_alert_count = sum(
        1 for n in home_notifications if n['kind'] == 'cheque_alert'
    )
    booking_alert_count = sum(
        1 for n in home_notifications if n['kind'] == 'booking_alert'
    )
    task_alert_count = sum(
        1 for n in home_notifications if n['kind'] in ('task_alert', 'task_overdue')
    )
    reminder_alert_count = sum(
        1 for n in home_notifications if n['kind'] in ('reminder_alert', 'reminder_overdue')
    )

    month_starts = []
    cursor = today.replace(day=1)
    for _ in range(6):
        month_starts.append(cursor)
        previous_year = cursor.year if cursor.month > 1 else cursor.year - 1
        previous_month = cursor.month - 1 if cursor.month > 1 else 12
        cursor = cursor.replace(year=previous_year, month=previous_month, day=1)
    month_starts.reverse()

    petty_rows = (
        CashSale.objects
        .filter(date__gte=month_starts[0])
        .annotate(month=TruncMonth('date'))
        .values('month', 'sale_type')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    petty_map = {}
    for row in petty_rows:
        key = (row['month'].year, row['month'].month)
        if key not in petty_map:
            petty_map[key] = {'cash_in': 0.0, 'cash_out': 0.0}
        if row['sale_type'] == CashSale.CASH_IN:
            petty_map[key]['cash_in'] = float(row['total'] or 0)
        else:
            petty_map[key]['cash_out'] = float(row['total'] or 0)

    chart_labels = [item.strftime('%b %Y') for item in month_starts]
    petty_in_values = []
    petty_out_values = []
    petty_net_values = []

    for month_start in month_starts:
        key = (month_start.year, month_start.month)
        petty_data = petty_map.get(key, {'cash_in': 0.0, 'cash_out': 0.0})

        petty_in_values.append(petty_data['cash_in'])
        petty_out_values.append(petty_data['cash_out'])
        petty_net_values.append(petty_data['cash_in'] - petty_data['cash_out'])

    # â”€â”€ Billing analytics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    billing_month_revenue = (
        Bill.objects
        .filter(status=Bill.COMPLETED, bill_date__year=today.year, bill_date__month=today.month)
        .aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    )
    pending_bills_qs = Bill.objects.filter(status=Bill.PENDING)
    pending_bills_count = pending_bills_qs.count()
    pending_bills_amount = (
        pending_bills_qs.aggregate(total=Sum('amount_due'))['total'] or Decimal('0')
    )
    pending_bookings_count = BookingOrder.objects.filter(status=BookingOrder.PENDING).count()

    billing_rows = (
        Bill.objects
        .filter(status=Bill.COMPLETED, bill_date__gte=month_starts[0])
        .annotate(month=TruncMonth('bill_date'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )
    billing_map = {
        (row['month'].year, row['month'].month): float(row['total'] or 0)
        for row in billing_rows
    }
    billing_revenue_values = [
        billing_map.get((ms.year, ms.month), 0.0) for ms in month_starts
    ]

    top_customers_qs = (
        Bill.objects
        .filter(status=Bill.COMPLETED)
        .values('customer__name')
        .annotate(total=Sum('total_amount'))
        .order_by('-total')[:5]
    )
    top_customer_names = [row['customer__name'] or 'Unknown' for row in top_customers_qs]
    top_customer_amounts = [float(row['total'] or 0) for row in top_customers_qs]

    pay_breakdown = (
        Payment.objects
        .values('method')
        .annotate(total=Sum('amount'))
    )
    pay_map = {row['method']: float(row['total'] or 0) for row in pay_breakdown}
    pay_method_values = [
        pay_map.get(Payment.CASH, 0.0),
        pay_map.get(Payment.CHEQUE, 0.0),
        pay_map.get(Payment.BALANCE, 0.0),
    ]

    context = {
        'today': today,
        'total_products': total_products,
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,
        'petty_cash_month_in': petty_cash_month_in,
        'petty_cash_month_out': petty_cash_month_out,
        'petty_cash_month_net': petty_cash_month_net,
        'current_month_start': current_month_start,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'critical_stock_count': critical_stock_count,
        'healthy_stock_count': total_products - low_stock_count,
        'recent_tasks': recent_tasks,
        'recent_tasks_count': len(recent_tasks),
        'low_stock_items': low_stock_items,
        'low_stock_limit': LOW_STOCK_LIMIT,
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'home_notifications': home_notifications,
        'home_notifications_count': len(home_notifications),
        'cheque_alert_count': cheque_alert_count,
        'booking_alert_count': booking_alert_count,
        'task_alert_count': task_alert_count,
        'reminder_alert_count': reminder_alert_count,
        'notification_sound_path': NOTIFICATION_SOUND_PATH,
        'chart_labels': chart_labels,
        'petty_in_values': petty_in_values,
        'petty_out_values': petty_out_values,
        'petty_net_values': petty_net_values,
        'stock_mix_values': [
            total_products - low_stock_count,
            low_stock_count - critical_stock_count - out_of_stock_count,
            critical_stock_count,
            out_of_stock_count,
        ],
        'billing_month_revenue': billing_month_revenue,
        'pending_bills_count': pending_bills_count,
        'pending_bills_amount': pending_bills_amount,
        'pending_bookings_count': pending_bookings_count,
        'billing_revenue_values': billing_revenue_values,
        'top_customer_names': top_customer_names,
        'top_customer_amounts': top_customer_amounts,
        'pay_method_values': pay_method_values,
    }
    return render(request, 'home.html', context)


def all_logs(request):
    selected_category = _selected_log_category(request)
    selected_user_id = request.GET.get('user', '').strip()
    date_from, date_to = resolve_date_range(request)

    qs = ActivityLog.objects.select_related('user').all()

    if selected_category != 'all':
        qs = qs.filter(category=selected_category)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    is_superadmin = False
    try:
        is_superadmin = request.user.profile.is_superadmin()
    except Exception:
        pass

    if is_superadmin and selected_user_id:
        try:
            qs = qs.filter(user_id=int(selected_user_id))
        except (ValueError, TypeError):
            pass

    total_logs = ActivityLog.objects.count()
    filtered_count = qs.count()

    paginator = Paginator(qs, 15)
    logs_page = paginator.get_page(request.GET.get('page'))

    all_users = User.objects.filter(is_active=True).order_by('username') if is_superadmin else []

    context = {
        'logs_page': logs_page,
        'total_logs': total_logs,
        'filtered_logs_count': filtered_count,
        'selected_category': selected_category,
        'selected_category_label': LOG_CATEGORY_CHOICES.get(selected_category, 'All Categories'),
        'log_categories': LOG_CATEGORY_CHOICES,
        'is_superadmin': is_superadmin,
        'all_users': all_users,
        'selected_user_id': selected_user_id,
        'reversible_actions': REVERSIBLE_ACTIONS,
        'reversal_effect_json': __import__('json').dumps(REVERSAL_EFFECT),
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'logs/all_logs.html', context)


def _get_activity_log_qs(request):
    selected_category = _selected_log_category(request)
    selected_user_id = request.GET.get('user', '').strip()
    date_from, date_to = resolve_date_range(request)
    qs = ActivityLog.objects.select_related('user').all()
    if selected_category != 'all':
        qs = qs.filter(category=selected_category)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)
    try:
        if request.user.profile.is_superadmin() and selected_user_id:
            qs = qs.filter(user_id=int(selected_user_id))
    except Exception:
        pass
    return qs, selected_category


def all_logs_export_pdf(request):
    qs, selected_category = _get_activity_log_qs(request)
    label = LOG_CATEGORY_CHOICES.get(selected_category, 'All Categories')

    logs = [
        {
            'timestamp': log.timestamp,
            'category': log.category,
            'kind': log.action,
            'title': log.description[:100],
            'message': f"by {log.user.get_full_name() or log.user.username if log.user else 'system'}",
            'url': log.url,
        }
        for log in qs
    ]

    context = {
        'logs': logs,
        'selected_category_label': label,
        'generated_at': timezone.localtime(),
    }

    template = get_template('logs/all_logs_pdf.html')
    html = template.render(context)

    try:
        from xhtml2pdf import pisa

        response = HttpResponse(content_type='application/pdf')
        timestamp = timezone.localtime().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="all_logs_{timestamp}.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('PDF generation error', status=500)
        return response
    except ImportError:
        context['printable'] = True
        return render(request, 'logs/all_logs_pdf.html', context)


# â”€â”€â”€ Authentication views â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember  = request.POST.get('remember')
        next_url  = request.POST.get('next', '').strip() or '/'

        # Guard against open-redirect
        if not next_url.startswith('/'):
            next_url = '/'

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 7)  # 7 days
            else:
                request.session.set_expiry(0)                  # browser close
            ActivityLog.objects.create(
                user=user,
                category='system',
                action='user_login',
                description=f"User logged in: {user.username}",
                url='/',
            )
            return redirect(next_url)

        messages.error(request, 'Invalid username or password. Please try again.')

    context = {
        'next': request.GET.get('next', ''),
        'year': _dt.date.today().year,
    }
    return render(request, 'auth/login.html', context)


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_name':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name  = request.POST.get('last_name',  '').strip()
            user.save(update_fields=['first_name', 'last_name'])
            messages.success(request, 'Your name has been updated.')

        elif action == 'change_password':
            current  = request.POST.get('current_password', '')
            new_pw   = request.POST.get('new_password', '')
            confirm  = request.POST.get('confirm_password', '')

            if not user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif new_pw != confirm:
                messages.error(request, 'New passwords do not match.')
            elif len(new_pw) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                user.set_password(new_pw)
                user.save()
                update_session_auth_hash(request, user)   # keep user logged in
                messages.success(request, 'Password changed successfully.')

        return redirect('profile')

    return render(request, 'auth/profile.html')


def all_logs_export_excel(request):
    qs, selected_category = _get_activity_log_qs(request)
    label = LOG_CATEGORY_CHOICES.get(selected_category, 'All Categories')

    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse('Excel export dependency missing: openpyxl', status=500)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Activity Logs'

    generated_at = timezone.localtime()
    sheet.append(['Activity Logs Report'])
    sheet.append(['Generated At', generated_at.strftime('%d %b %Y %I:%M %p')])
    sheet.append(['Category Filter', label])
    sheet.append(['Total Rows', qs.count()])
    sheet.append([])
    sheet.append(['Timestamp', 'Category', 'Action', 'Description', 'User', 'URL'])

    for log in qs:
        user_label = ''
        if log.user:
            user_label = log.user.get_full_name() or log.user.username
        sheet.append([
            timezone.localtime(log.timestamp).strftime('%d %b %Y %I:%M %p'),
            LOG_CATEGORY_CHOICES.get(log.category, log.category).title(),
            log.action,
            log.description,
            user_label,
            log.url,
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    timestamp = timezone.localtime().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="activity_logs_{timestamp}.xlsx"'
    workbook.save(response)
    return response


# â”€â”€â”€ Log Reverse (SuperAdmin only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

REVERSIBLE_ACTIONS = frozenset({
    'bill_created',
    'customer_created',
    'product_created',
    'category_created',
    'machine_run_created',
    'cash_entry_created',
    'booking_created',
    'purchase_created',
    'user_created',
})

# Human-readable labels for what reversal does for each action
REVERSAL_EFFECT = {
    'bill_created':       'Cancel bill & restore inventory/balance',
    'customer_created':   'Delete customer record',
    'product_created':    'Delete product record',
    'category_created':   'Delete product category',
    'machine_run_created':'Delete machine run record',
    'cash_entry_created': 'Delete petty cash entry',
    'booking_created':    'Delete booking order',
    'purchase_created':   'Delete material purchase record',
    'user_created':       'Delete user account',
}


@superadmin_required
def log_reverse(request, log_pk):
    if request.method != 'POST':
        return redirect('all_logs')

    log = get_object_or_404(ActivityLog, pk=log_pk)

    if log.action not in REVERSIBLE_ACTIONS:
        messages.error(request, f'Action "{log.action}" cannot be reversed.')
        return redirect('all_logs')

    if not log.related_id:
        messages.error(request, 'This log entry has no linked object â€” it cannot be reversed automatically.')
        return redirect('all_logs')

    try:
        with transaction.atomic():
            _execute_reversal(log, request.user)
            log.delete()
        messages.success(request, f'Reversed: {log.description[:80]} â€” log entry cleared.')
    except Exception as exc:
        messages.error(request, f'Reversal failed: {exc}')

    return redirect('all_logs')


def _execute_reversal(log, acting_user):
    """Undo the recorded action and restore related data."""
    from django.db.models import F, ProtectedError
    from decimal import Decimal

    action = log.action
    rid    = log.related_id

    # â”€â”€ Bill created â†’ cancel it, restore inventory + customer balance â”€â”€
    if action == 'bill_created':
        try:
            bill = Bill.objects.select_for_update().get(pk=rid)
        except Bill.DoesNotExist:
            raise ValueError('Bill not found â€” it may have already been deleted or cancelled.')

        if bill.status == Bill.CANCELLED:
            raise ValueError(f'Bill {bill.bill_number} is already cancelled.')

        for item in bill.items.select_related('product').all():
            Product.objects.filter(pk=item.product.pk).update(qty=F('qty') + item.quantity)

        customer = Customer.objects.select_for_update().get(pk=bill.customer.pk)
        if bill.payment_method == Bill.PAY_LATER:
            customer.balance = customer.balance + bill.total_amount - bill.amount_paid + bill.balance_used
        else:
            overpay = max(Decimal('0'), bill.amount_paid - (bill.total_amount - bill.balance_used))
            customer.balance = customer.balance + bill.balance_used - overpay
        customer.save(update_fields=['balance'])

        bill.status = Bill.CANCELLED
        bill.save(update_fields=['status'])

    # â”€â”€ Customer created â†’ delete (only if no bills exist) â”€â”€
    elif action == 'customer_created':
        try:
            customer = Customer.objects.get(pk=rid)
        except Customer.DoesNotExist:
            raise ValueError('Customer not found â€” may have already been deleted.')
        try:
            customer.delete()
        except ProtectedError:
            raise ValueError(f'Cannot reverse: customer "{customer.name}" has linked billing records.')

    # â”€â”€ Product created â†’ delete (only if not referenced in bills) â”€â”€
    elif action == 'product_created':
        try:
            product = Product.objects.get(pk=rid)
        except Product.DoesNotExist:
            raise ValueError('Product not found â€” may have already been deleted.')
        try:
            product.delete()
        except ProtectedError:
            raise ValueError(f'Cannot reverse: product "{product.name}" is referenced in billing records.')

    # â”€â”€ Category created â†’ delete â”€â”€
    elif action == 'category_created':
        try:
            cat = ProductCategory.objects.get(pk=rid)
        except ProductCategory.DoesNotExist:
            raise ValueError('Category not found â€” may have already been deleted.')
        try:
            cat.delete()
        except ProtectedError:
            raise ValueError(f'Cannot reverse: category "{cat.name}" still has products.')

    # â”€â”€ Machine run created â†’ delete â”€â”€
    elif action == 'machine_run_created':
        try:
            run = DailyRunningMachine.objects.get(pk=rid)
            run.delete()
        except DailyRunningMachine.DoesNotExist:
            raise ValueError('Machine run record not found â€” may have already been deleted.')

    # â”€â”€ Petty cash entry created â†’ delete â”€â”€
    elif action == 'cash_entry_created':
        try:
            entry = CashSale.objects.get(pk=rid)
            entry.delete()
        except CashSale.DoesNotExist:
            raise ValueError('Petty cash entry not found â€” may have already been deleted.')

    # â”€â”€ Booking created â†’ delete â”€â”€
    elif action == 'booking_created':
        try:
            booking = BookingOrder.objects.get(pk=rid)
            booking.delete()
        except BookingOrder.DoesNotExist:
            raise ValueError('Booking not found â€” may have already been deleted.')

    # â”€â”€ Material purchase created â†’ delete â”€â”€
    elif action == 'purchase_created':
        try:
            purchase = MaterialPurchase.objects.get(pk=rid)
            purchase.delete()
        except MaterialPurchase.DoesNotExist:
            raise ValueError('Purchase record not found â€” may have already been deleted.')

    # â”€â”€ User created â†’ delete â”€â”€
    elif action == 'user_created':
        try:
            target = User.objects.get(pk=rid)
        except User.DoesNotExist:
            raise ValueError('User not found â€” may have already been deleted.')
        if target == acting_user:
            raise ValueError('You cannot reverse the creation of your own account.')
        target.delete()

    else:
        raise ValueError(f'Unknown reversible action: {action}')


# â”€â”€â”€ User Management (SuperAdmin only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@superadmin_required
def user_list(request):
    users = User.objects.select_related('profile').filter(is_active=True).order_by('username')
    return render(request, 'users/user_list.html', {'users': users})


@superadmin_required
def user_create(request):
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        password   = request.POST.get('password', '')
        confirm    = request.POST.get('confirm_password', '')
        role       = request.POST.get('role', UserProfile.ADMIN)

        if not username:
            messages.error(request, 'Username is required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif role not in (UserProfile.SUPERADMIN, UserProfile.ADMIN):
            messages.error(request, 'Invalid role selected.')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(user=user, role=role)
            from .utils import log_activity
            log_activity(
                request, 'users', 'user_created',
                f"User created: {username} ({dict(UserProfile.ROLE_CHOICES)[role]})",
                reverse('user_list'),
                related_id=user.pk,
            )
            messages.success(request, f'User "{username}" created successfully.')
            return redirect('user_list')

    return render(request, 'users/user_form.html', {
        'form_title': 'Create New User',
        'role_choices': UserProfile.ROLE_CHOICES,
        'submit_label': 'Create User',
    })


@superadmin_required
def user_edit(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        role       = request.POST.get('role', UserProfile.ADMIN)
        new_pw     = request.POST.get('new_password', '').strip()
        confirm    = request.POST.get('confirm_password', '').strip()

        if role not in (UserProfile.SUPERADMIN, UserProfile.ADMIN):
            messages.error(request, 'Invalid role selected.')
        elif new_pw and len(new_pw) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif new_pw and new_pw != confirm:
            messages.error(request, 'Passwords do not match.')
        else:
            target_user.first_name = first_name
            target_user.last_name  = last_name
            target_user.save(update_fields=['first_name', 'last_name'])
            profile.role = role
            profile.save(update_fields=['role'])
            if new_pw:
                target_user.set_password(new_pw)
                target_user.save()
            from .utils import log_activity
            log_activity(
                request, 'users', 'user_updated',
                f"User updated: {target_user.username} ({dict(UserProfile.ROLE_CHOICES)[role]})",
                reverse('user_list'),
            )
            messages.success(request, f'User "{target_user.username}" updated successfully.')
            return redirect('user_list')

    return render(request, 'users/user_form.html', {
        'form_title': f'Edit User: {target_user.username}',
        'target_user': target_user,
        'profile': profile,
        'role_choices': UserProfile.ROLE_CHOICES,
        'submit_label': 'Save Changes',
        'is_edit': True,
    })


@superadmin_required
def user_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')
    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        from .utils import log_activity
        log_activity(
            request, 'users', 'user_deleted',
            f"User deleted: {username}",
            reverse('user_list'),
        )
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('user_list')
    return render(request, 'users/user_confirm_delete.html', {'target_user': target_user})

@superadmin_required
def company_settings_view(request):
    instance = CompanySettings.get()
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company settings saved.')
            return redirect('company_settings')
    else:
        form = CompanySettingsForm(instance=instance)
    return render(request, 'company_settings.html', {'form': form, 'company': instance})
