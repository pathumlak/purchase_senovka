from django.urls import path

from . import views

urlpatterns = [
    path('',                 views.reminder_list,   name='reminder_list'),
    path('create/',          views.reminder_create, name='reminder_create'),
    path('<int:pk>/edit/',   views.reminder_edit,   name='reminder_edit'),
    path('<int:pk>/delete/', views.reminder_delete, name='reminder_delete'),
    path('<int:pk>/done/',   views.reminder_done,   name='reminder_done'),
]
