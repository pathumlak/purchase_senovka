from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('',                  views.vehicle_log_list,    name='list'),
    path('<int:pk>/edit/',    views.vehicle_log_edit,    name='edit'),
    path('<int:pk>/delete/',  views.vehicle_log_delete,  name='delete'),
    path('export/excel/',     views.vehicle_export_excel, name='export_excel'),
    path('export/pdf/',       views.vehicle_export_pdf,   name='export_pdf'),
]
