from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import DoctorProfile

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['booking:doctor_list']

    def location(self, item):
        return reverse(item)

class DoctorProfileSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return DoctorProfile.objects.all()

    def lastmod(self, obj):
        # Assuming you have a field that tracks the last modification time of the profile.
        # If not, you can remove this method.
        return None
