from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.task_board,         name='task_board'),
    path('create/',                 views.task_create,        name='task_create'),
    path('<int:pk>/edit/',          views.task_edit,          name='task_edit'),
    path('<int:pk>/delete/',        views.task_delete,        name='task_delete'),
    path('<int:pk>/status/',        views.task_status_update, name='task_status_update'),
]
