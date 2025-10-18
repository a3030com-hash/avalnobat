from django.urls import path, re_path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('doctor/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('doctor/<int:pk>/book/<str:date>/', views.book_appointment, name='book_appointment'),
    path('verify/', views.verify_appointment, name='verify_appointment'),
    path('payment/', views.payment_page, name='payment_page'),
    path('confirm/', views.confirm_payment, name='confirm_payment'),
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('availability/<int:pk>/edit/', views.edit_availability, name='edit_availability'),
    path('availability/<int:pk>/delete/', views.delete_availability, name='delete_availability'),
    path('availability/<int:pk>/toggle/', views.toggle_availability, name='toggle_availability'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    re_path(r'^secretary-panel/(?P<date>\d{4}-\d{2}-\d{2})?/?$', views.secretary_panel, name='secretary_panel'),
    re_path(r'^daily-patients/(?P<date>\d{4}-\d{2}-\d{2})?/?$', views.daily_patients, name='daily_patients'),
    re_path(r'^secretary-payments/(?P<date>\d{4}-\d{2}-\d{2})?/?$', views.secretary_payments, name='secretary_payments'),
    re_path(r'^financial-report/(?P<date>\d{4}-\d{2}-\d{2})?/?$', views.financial_report, name='financial_report'),
    path('manual-booking/<str:date>/', views.manual_booking, name='manual_booking'),
    path('cancel-slot/<str:slot>/', views.cancel_slot, name='cancel_slot'),
]