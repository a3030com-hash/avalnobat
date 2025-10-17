from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Specialty, DoctorProfile, DoctorAvailability, Appointment, Review

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type',)}),
    )

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'phone_number')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialty__name')
    list_filter = ('specialty',)

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'get_day_of_week_display', 'shift', 'start_time', 'end_time', 'is_active')
    list_filter = ('doctor', 'day_of_week', 'shift', 'is_active')
    search_fields = ('doctor__user__username',)

    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_of_week_display.short_description = 'روز هفته'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor', 'appointment_datetime', 'status')
    list_filter = ('status', 'doctor', 'appointment_datetime')
    search_fields = ('patient_name', 'doctor__user__username', 'patient__username')
    date_hierarchy = 'appointment_datetime'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'rating')
    list_filter = ('rating',)
    search_fields = ('appointment__patient_name',)

admin.site.register(CustomUser, CustomUserAdmin)