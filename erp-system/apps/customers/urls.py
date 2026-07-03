from django.urls import path
from . import views

urlpatterns = [
    # Customer CRUD
    path('', views.customer_list, name='customer_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('<int:pk>/update-balance/', views.customer_update_balance, name='customer_update_balance'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('<int:pk>/settle/', views.customer_settle_balance, name='customer_settle_balance'),

    # Customer Product Pricing CRUD
    path('pricing/', views.customer_pricing_list, name='customer_pricing_list'),
    path('pricing/create/', views.pricing_create, name='pricing_create'),
    path('pricing/export/excel/', views.pricing_export_excel, name='pricing_export_excel'),
    path('pricing/export/pdf/', views.pricing_export_pdf, name='pricing_export_pdf'),
    path('pricing/<int:pk>/edit/', views.pricing_update, name='pricing_update'),
    path('pricing/<int:pk>/delete/', views.pricing_delete, name='pricing_delete'),

    # Bulk pricing
    path('pricing/bulk/', views.bulk_pricing_view, name='bulk_pricing_view'),
    path('pricing/bulk/save/', views.bulk_pricing_save, name='bulk_pricing_save'),

    # Customer Balances Report
    path('balances/', views.customer_balances_report, name='customer_balances_report'),
    path('balances/export/excel/', views.customer_balances_export_excel, name='customer_balances_export_excel'),
    path('balances/export/pdf/', views.customer_balances_export_pdf, name='customer_balances_export_pdf'),

    # Ledger
    path('<int:pk>/ledger/', views.customer_ledger, name='customer_ledger'),
    path('<int:pk>/ledger/export/excel/', views.customer_ledger_export_excel, name='customer_ledger_export_excel'),
    path('<int:pk>/ledger/export/pdf/', views.customer_ledger_export_pdf, name='customer_ledger_export_pdf'),

    # API
    path('api/price/', views.get_customer_price, name='get_customer_price'),
    path('api/search/', views.customer_search_api, name='customer_search_api'),
    path('api/customer-products/', views.customer_products_api, name='customer_products_api'),
]
