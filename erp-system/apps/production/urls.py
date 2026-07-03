from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('', views.category_list, name='category_list'),
    path('category/export/pdf/', views.category_export_pdf, name='category_export_pdf'),
    path('category/export/excel/', views.category_export_excel, name='category_export_excel'),
    path('category/new/', views.category_create, name='category_create'),
    path('category/<int:pk>/edit/', views.category_update, name='category_edit'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Daily Running Machines
    path('daily-machines/', views.daily_machine_list, name='daily_machine_list'),
    path('daily-machines/export/pdf/', views.daily_machine_export_pdf, name='daily_machine_export_pdf'),
    path('daily-machines/export/excel/', views.daily_machine_export_excel, name='daily_machine_export_excel'),
    path('daily-machines/new/', views.daily_machine_create, name='daily_machine_create'),
    path('daily-machines/<int:pk>/edit/', views.daily_machine_update, name='daily_machine_edit'),
    path('daily-machines/<int:pk>/delete/', views.daily_machine_delete, name='daily_machine_delete'),

    # Machines
    path('machines/new/', views.machine_create, name='machine_create'),
    path('machines/<int:pk>/edit/', views.machine_update, name='machine_edit'),
    path('machines/<int:pk>/delete/', views.machine_delete, name='machine_delete'),

    # Daily Work Assignments
    path('work-assignments/save/', views.work_assignment_save, name='work_assignment_save'),
    path('work-assignments/<int:pk>/delete/', views.work_assignment_delete, name='work_assignment_delete'),

    # Production Entries (daily qty updates)
    path('entries/', views.production_entry_list, name='production_entry_list'),
    path('entries/add/', views.production_entry_create, name='production_entry_create'),
    path('entries/<int:pk>/edit/', views.production_entry_edit, name='production_entry_edit'),
    path('entries/<int:pk>/delete/', views.production_entry_delete, name='production_entry_delete'),
    path('entries/export/excel/', views.production_entry_export_excel, name='production_entry_export_excel'),
    path('entries/export/pdf/', views.production_entry_export_pdf, name='production_entry_export_pdf'),

    # Stock Ledger (production additions + bill deductions, running balance)
    path('stock-ledger/', views.stock_ledger, name='stock_ledger'),
    path('stock-ledger/export/excel/', views.stock_ledger_export_excel, name='stock_ledger_export_excel'),
    path('stock-ledger/export/pdf/', views.stock_ledger_export_pdf, name='stock_ledger_export_pdf'),

    # All Production Report (live snapshot of every product's available qty)
    path('all-production-report/', views.all_production_report, name='all_production_report'),
    path('all-production-report/export/excel/', views.all_production_report_export_excel, name='all_production_report_export_excel'),
    path('all-production-report/export/pdf/', views.all_production_report_export_pdf, name='all_production_report_export_pdf'),

    # ── Target Log System ─────────────────────────────────────
    path('target-logs/', views.target_log_list, name='target_log_list'),
    path('target-logs/create/', views.target_log_create, name='target_log_create'),
    path('target-logs/<int:pk>/update/', views.target_log_update_inline, name='target_log_update_inline'),
    path('target-logs/<int:pk>/delete/', views.target_log_delete, name='target_log_delete'),
    path('target-logs/calc/', views.target_log_calc_api, name='target_log_calc_api'),
    path('target-logs/points/', views.target_log_points_report, name='target_log_points_report'),
    path('target-logs/export/excel/', views.target_log_export_excel, name='target_log_export_excel'),
    path('target-logs/export/pdf/', views.target_log_export_pdf, name='target_log_export_pdf'),
    path('target-logs/points/pdf/', views.target_log_points_pdf, name='target_log_points_pdf'),
    path('target-logs/points/excel/', views.target_log_points_excel, name='target_log_points_excel'),

    # Production Items (for Target Log)
    path('production-items/create/', views.production_item_create, name='production_item_create'),
    path('production-items/<int:pk>/update/', views.production_item_update, name='production_item_update'),
    path('production-items/<int:pk>/delete/', views.production_item_delete, name='production_item_delete'),

    # Shift Templates (for Target Log)
    path('shift-templates/create/', views.shift_template_create, name='shift_template_create'),
    path('shift-templates/<int:pk>/update/', views.shift_template_update, name='shift_template_update'),
    path('shift-templates/<int:pk>/delete/', views.shift_template_delete, name='shift_template_delete'),

    # ── Shift Production Log System ───────────────────────────
    path('shift-logs/', views.shift_log_list, name='shift_log_list'),
    path('shift-logs/create/', views.shift_log_create, name='shift_log_create'),
    path('shift-logs/<int:pk>/update/', views.shift_log_update_inline, name='shift_log_update_inline'),
    path('shift-logs/<int:pk>/delete/', views.shift_log_delete, name='shift_log_delete'),
    path('shift-logs/points/', views.shift_log_points_report, name='shift_log_points_report'),
    path('shift-logs/export/excel/', views.shift_log_export_excel, name='shift_log_export_excel'),
    path('shift-logs/export/pdf/', views.shift_log_export_pdf, name='shift_log_export_pdf'),
    path('shift-logs/points/pdf/', views.shift_log_points_pdf, name='shift_log_points_pdf'),
    path('shift-logs/points/excel/', views.shift_log_points_excel, name='shift_log_points_excel'),

    # Employees
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
]
