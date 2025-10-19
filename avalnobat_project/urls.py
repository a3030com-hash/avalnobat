from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from booking import views as booking_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('booking.urls', namespace='booking')),

    # Auth URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='booking/login.html',
        redirect_authenticated_user=True # اگر کاربر لاگین کرده باشد، به صفحه دیگری هدایت می‌شود
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='booking:doctor_list' # پس از خروج به صفحه اصلی می‌رود
    ), name='logout'),

    path('signup/', booking_views.doctor_signup, name='signup'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='booking/password_reset_form.html',
        email_template_name='booking/password_reset_email.html',
        subject_template_name='booking/password_reset_subject.txt',
        success_url='/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='booking/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='booking/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='booking/password_reset_complete.html'
    ), name='password_reset_complete'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)