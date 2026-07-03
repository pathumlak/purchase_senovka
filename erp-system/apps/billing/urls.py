from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('',                         views.bill_list,        name='bill_list'),
    path('create/',                  views.bill_create,      name='bill_create'),
    path('<int:pk>/',                views.bill_detail,      name='bill_detail'),
    path('<int:pk>/edit/',           views.bill_edit,        name='bill_edit'),
    path('<int:pk>/cancel/',         views.bill_cancel,      name='bill_cancel'),
    path('<int:pk>/settle/',         views.settle_bill,      name='settle_bill'),
    path('<int:pk>/print/',          views.bill_print,       name='bill_print'),
    path('pending/',                 views.pending_bills,    name='pending_bills'),
    path('hold/',                    views.hold_bill_create,   name='hold_bill_create'),
    path('held/',                    views.held_bills_list,    name='held_bills'),
    path('held/<int:pk>/recall/',    views.held_bill_recall,   name='held_bill_recall'),
    path('held/<int:pk>/delete/',    views.held_bill_delete,   name='held_bill_delete'),
    path('export/excel/',            views.bill_export_excel,name='export_excel'),
    path('export/pdf/',              views.bill_export_pdf,  name='export_pdf'),
    path('api/customer/<int:pk>/',   views.api_customer_info,name='api_customer_info'),

    # Sales views
    path('sales/cash/',                    views.cash_sales_list,           name='cash_sales'),
    path('sales/cash/export/excel/',       views.cash_sales_export_excel,   name='cash_sales_excel'),
    path('sales/cash/export/pdf/',         views.cash_sales_export_pdf,     name='cash_sales_pdf'),
    path('sales/cheque/',                         views.cheque_sales_list,          name='cheque_sales'),
    path('sales/cheque/export/excel/',            views.cheque_sales_export_excel,  name='cheque_sales_excel'),
    path('sales/cheque/export/pdf/',              views.cheque_sales_export_pdf,    name='cheque_sales_pdf'),
    path('sales/cheque/<int:pk>/status/',         views.cheque_update_status,       name='cheque_update_status'),
    path('payments/<int:pk>/edit-dates/',         views.payment_update_dates,       name='payment_update_dates'),
    path('payments/<int:pk>/delete/',             views.payment_delete,             name='payment_delete'),
    path('sales/split/',                   views.split_sales_list,          name='split_sales'),
    path('sales/split/export/excel/',      views.split_sales_export_excel,  name='split_sales_excel'),
    path('sales/split/export/pdf/',        views.split_sales_export_pdf,    name='split_sales_pdf'),
]
