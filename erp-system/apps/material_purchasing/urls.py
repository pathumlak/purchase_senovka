from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('',                        views.purchase_list,          name='purchase_list'),
    path('new/',                    views.purchase_create,        name='purchase_create'),
    path('<int:pk>/edit/',          views.purchase_update,        name='purchase_edit'),
    path('<int:pk>/delete/',        views.purchase_delete,        name='purchase_delete'),
    path('export/excel/',           views.purchase_export_excel,  name='export_excel'),
    path('export/pdf/',             views.purchase_export_pdf,    name='export_pdf'),
]
