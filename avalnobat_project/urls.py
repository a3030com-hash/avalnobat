from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from booking import views as booking_views
from django.contrib.sitemaps.views import sitemap
from booking.sitemaps import StaticViewSitemap, DoctorProfileSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'doctors': DoctorProfileSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', include('robots.urls')),

    # App URLs
    path('', include('booking.urls', namespace='booking')),

    # Auth URLs
    path('login/', booking_views.CustomLoginView.as_view(
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='booking:doctor_list' # پس از خروج به صفحه اصلی می‌رود
    ), name='logout'),

]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)