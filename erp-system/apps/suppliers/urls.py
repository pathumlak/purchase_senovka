from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('',                          views.supplier_list,   name='supplier_list'),
    path('new/',                      views.supplier_create, name='supplier_create'),
    path('<int:pk>/',                 views.supplier_detail, name='supplier_detail'),
    path('<int:pk>/edit/',            views.supplier_edit,   name='supplier_edit'),
    path('<int:pk>/delete/',          views.supplier_delete, name='supplier_delete'),
    path('supply/record/',            views.supply_record,   name='supply_record'),
    path('supply/<int:pk>/',          views.supply_detail,   name='supply_detail'),
    path('supply/<int:pk>/delete/',   views.supply_delete,   name='supply_delete'),
    path('api/products/',             views.api_product_search, name='api_product_search'),

    # Purchase Orders
    path('orders/',                              views.purchase_order_list,    name='purchase_order_list'),
    path('orders/new/',                          views.purchase_order_create,  name='purchase_order_create'),
    path('orders/<int:pk>/',                     views.purchase_order_detail,  name='purchase_order_detail'),
    path('orders/<int:pk>/receive/',             views.purchase_order_receive, name='purchase_order_receive'),
    path('orders/<int:pk>/cancel/',              views.purchase_order_cancel,  name='purchase_order_cancel'),
    path('orders/<int:pk>/delete/',              views.purchase_order_delete,  name='purchase_order_delete'),
    path('orders/<int:pk>/pdf/',                 views.purchase_order_pdf,     name='purchase_order_pdf'),
    path('orders/<int:pk>/excel/',               views.purchase_order_excel,   name='purchase_order_excel'),
]
