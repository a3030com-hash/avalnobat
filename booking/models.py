import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("PATIENT", "Patient"),
        ("DOCTOR", "Doctor"),
        ("ADMIN", "Admin"),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="PATIENT")

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="نام تخصص")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"

class DoctorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="تخصص")
    address = models.TextField(verbose_name="آدرس مطب", null=True, blank=True)
    phone_number = models.CharField(max_length=20, verbose_name="شماره تلفن مطب", null=True, blank=True)
    photo = models.ImageField(upload_to='doctor_photos/', null=True, blank=True, verbose_name="عکس پزشک")
    biography = models.TextField(blank=True, verbose_name="بیوگرافی")

    def __str__(self):
        return f"دکتر {self.user.get_full_name()}"

    class Meta:
        verbose_name = "پروفایل پزشک"
        verbose_name_plural = "پروفایل پزشکان"

class DoctorAvailability(models.Model):
    SHIFT_CHOICES = (
        ('MORNING', 'صبح'),
        ('AFTERNOON', 'بعدازظهر'),
    )
    DAY_CHOICES = (
        (5, 'شنبه'),
        (6, 'یکشنبه'),
        (0, 'دوشنبه'),
        (1, 'سه‌شنبه'),
        (2, 'چهارشنبه'),
        (3, 'پنجشنبه'),
        (4, 'جمعه'),
    )

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availabilities', verbose_name="پزشک")
    day_of_week = models.IntegerField(choices=DAY_CHOICES, verbose_name="روز هفته")
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, verbose_name="شیفت کاری")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")
    visit_count = models.PositiveIntegerField(default=20, verbose_name="تعداد ویزیت")
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} {self.get_shift_display()}"

    class Meta:
        verbose_name = "زمان‌بندی پزشک"
        verbose_name_plural = "زمان‌بندی پزشکان"
        unique_together = ('doctor', 'day_of_week', 'shift')

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('BOOKED', 'رزرو شده'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELED', 'لغو شده'),
        ('PENDING_PAYMENT', 'در انتظار پرداخت'),
    )
    INSURANCE_CHOICES = (
        ('TAMIN', 'تامین اجتماعی'),
        ('SALAMAT', 'سلامت'),
        ('KHADAMAT', 'خدمات درمانی'),
        ('ARTESH', 'ارتش'),
        ('AZAD', 'آزاد'),
    )

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments', verbose_name="پزشک")
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments', verbose_name="بیمار", null=True, blank=True)
    appointment_datetime = models.DateTimeField(verbose_name="زمان نوبت")
    patient_name = models.CharField(max_length=100, verbose_name="نام بیمار")
    patient_phone = models.CharField(max_length=20, verbose_name="شماره همراه بیمار")
    patient_national_id = models.CharField(max_length=10, verbose_name="کد ملی بیمار", null=True, blank=True)
    insurance_type = models.CharField(max_length=10, choices=INSURANCE_CHOICES, verbose_name="نوع بیمه", default='AZAD')
    problem_description = models.TextField(blank=True, verbose_name="شرح مشکل")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    created_at = models.DateTimeField(auto_now_add=True)

    # Fields for secretary panel
    PAYMENT_METHOD_CHOICES = (
        (1, 'کارت خوان'),
        (2, 'نقدی'),
        (3, 'کارت به کارت'),
        (4, 'رایگان'),
    )
    visit_fee_paid = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="مبلغ ویزیت دریافتی")
    service_description = models.CharField(max_length=255, default="حق ویزیت", verbose_name="شرح خدمات")
    payment_method = models.IntegerField(choices=PAYMENT_METHOD_CHOICES, null=True, blank=True, verbose_name="نوع پرداخت")

    def __str__(self):
        return f"نوبت برای {self.patient_name} نزد {self.doctor} در تاریخ {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "نوبت"
        verbose_name_plural = "نوبت‌ها"
        ordering = ['-appointment_datetime']

class Review(models.Model):
    RATING_CHOICES = (
        (1, '۱ ستاره'),
        (2, '۲ ستاره'),
        (3, '۳ ستاره'),
        (4, '۴ ستاره'),
        (5, '۵ ستاره'),
    )

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review', verbose_name="نوبت مربوطه")
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="امتیاز")
    comment = models.TextField(blank=True, verbose_name="نظر")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"نظر برای نوبت شماره {self.appointment.id}"

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"

class DailyExpense(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='expenses', verbose_name="پزشک")
    date = models.DateField(default=datetime.date.today, verbose_name="تاریخ")
    description = models.CharField(max_length=255, verbose_name="شرح هزینه/پرداخت")
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.amount} در تاریخ {self.date}"

    class Meta:
        verbose_name = "هزینه/پرداخت روزانه"
        verbose_name_plural = "هزینه‌ها و پرداخت‌های روزانه"
        ordering = ['-date', '-created_at']

class TimeSlotException(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='exceptions')
    datetime_slot = models.DateTimeField(verbose_name="بازه زمانی")
    is_cancellation = models.BooleanField(default=True)

    def __str__(self):
        return f"اسلات لغو شده برای {self.doctor} در {self.datetime_slot}"

    class Meta:
        verbose_name = "استثناء زمانی"
        verbose_name_plural = "استثناهای زمانی"
        unique_together = ('doctor', 'datetime_slot')

class InsuranceFee(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='insurance_fees', verbose_name="پزشک")
    insurance_type = models.CharField(max_length=10, choices=Appointment.INSURANCE_CHOICES, verbose_name="نوع بیمه")
    fee = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="مبلغ ویزیت")

    def __str__(self):
        return f"هزینه بیمه {self.get_insurance_type_display()} برای {self.doctor}"

    class Meta:
        verbose_name = "هزینه بیمه"
        verbose_name_plural = "هزینه‌های بیمه"
        unique_together = ('doctor', 'insurance_type')