from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

urlpatterns = [
    # Auth
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Main pages
    path('', views.home, name='home'),
    path('logs/', views.all_logs, name='all_logs'),
    path('logs/<int:log_pk>/reverse/', views.log_reverse, name='log_reverse'),
    path('logs/export/pdf/', views.all_logs_export_pdf, name='all_logs_export_pdf'),
    path('logs/export/excel/', views.all_logs_export_excel, name='all_logs_export_excel'),

    # User management (SuperAdmin only)
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('settings/company/', views.company_settings_view, name='company_settings'),

    path('admin/', admin.site.urls),
    path('production/', include('apps.production.urls')),
    path('customers/', include('apps.customers.urls')),
path('pettycash/', include(('apps.pettycash.urls', 'pettycash'), namespace='pettycash')),
    path('purchasing/', include(('apps.material_purchasing.urls', 'purchasing'), namespace='purchasing')),
    path('billing/',   include(('apps.billing.urls', 'billing'), namespace='billing')),
    path('booking/',   include('apps.booking.urls', namespace='booking')),
    path('suppliers/', include(('apps.suppliers.urls', 'suppliers'), namespace='suppliers')),
    path('tasks/',    include('apps.tasks.urls')),
    path('vehicles/', include(('apps.vehicles.urls', 'vehicles'), namespace='vehicles')),
    path('reminders/', include('apps.reminders.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)