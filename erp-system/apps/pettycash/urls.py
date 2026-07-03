from django.urls import path
from . import views

app_name = 'pettycash'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('export/monthly/pdf/', views.monthly_export_pdf, name='monthly_export_pdf'),
    path('export/monthly/excel/', views.monthly_export_excel, name='monthly_export_excel'),
    path('new/', views.sale_create, name='sale_create'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/edit/', views.sale_update, name='sale_edit'),
    path('<int:pk>/delete/', views.sale_delete, name='sale_delete'),
]