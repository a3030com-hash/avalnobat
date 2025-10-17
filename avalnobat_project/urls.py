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
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)