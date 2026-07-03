from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('',                          views.booking_list,            name='booking_list'),
    path('create/',                   views.booking_create,          name='booking_create'),
    path('<int:pk>/',                 views.booking_detail,          name='booking_detail'),
    path('<int:pk>/confirm/',         views.booking_confirm,         name='booking_confirm'),
    path('<int:pk>/cancel/',          views.booking_cancel,          name='booking_cancel'),
    path('<int:pk>/quotation/pdf/',   views.booking_quotation_pdf,   name='quotation_pdf'),
    path('<int:pk>/quotation/excel/', views.booking_quotation_excel, name='quotation_excel'),
    path('export/excel/',             views.booking_export_excel,    name='export_excel'),
    path('export/pdf/',               views.booking_export_pdf,      name='export_pdf'),
    path('api/production-needs/',     views.api_production_needs,    name='api_production_needs'),
    path('print/selected/',           views.booking_print_selected,  name='print_selected'),
]
