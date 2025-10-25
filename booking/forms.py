from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from .models import DoctorAvailability, Appointment, Specialty, DoctorProfile

User = get_user_model()

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="نام", widget=forms.TextInput(attrs={'placeholder': 'نام'}))
    last_name = forms.CharField(max_length=30, required=True, label="نام خانوادگی", widget=forms.TextInput(attrs={'placeholder': 'نام خانوادگی'}))
    email = forms.EmailField(required=True, label="ایمیل", widget=forms.EmailInput(attrs={'placeholder': 'ایمیل'}))

    specialty = forms.ModelChoiceField(queryset=Specialty.objects.all(), required=True, label="تخصص")
    address = forms.CharField(max_length=255, required=True, label="آدرس مطب", widget=forms.TextInput(attrs={'placeholder': 'آدرس مطب'}))
    phone_number = forms.CharField(max_length=20, required=True, label="شماره تلفن مطب", widget=forms.TextInput(attrs={'placeholder': 'شماره تلفن مطب'}))
    medical_id = forms.CharField(max_length=20, required=True, label="شماره نظام پزشکی", widget=forms.TextInput(attrs={'placeholder': 'شماره نظام پزشکی'}))
    photo = forms.ImageField(required=False, label="عکس پروفایل")
    biography = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'بیوگرافی'}), required=False, label="بیوگرافی")

    def __init__(self, *args, **kwargs):
        super(DoctorRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'نام کاربری'
        self.fields['password2'].widget.attrs['placeholder'] = 'تکرار رمز عبور'
        self.fields['password2'].label = "تکرار رمز عبور"
        self.fields['password1'].widget.attrs['placeholder'] = 'رمز عبور'


    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'DOCTOR'
        if commit:
            user.save()
            # Create DoctorProfile
            DoctorProfile.objects.create(
                user=user,
                specialty=self.cleaned_data.get('specialty'),
                address=self.cleaned_data.get('address'),
                phone_number=self.cleaned_data.get('phone_number'),
                photo=self.cleaned_data.get('photo'),
                biography=self.cleaned_data.get('biography')
            )
        return user

class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ['day_of_week', 'shift', 'start_time', 'end_time', 'visit_count', 'is_active']
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'placeholder': 'HH:MM'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'placeholder': 'HH:MM'}),
        }
        labels = {
            'day_of_week': 'روز هفته',
            'shift': 'شیفت کاری',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان',
            'visit_count': 'تعداد ویزیت',
            'is_active': 'فعال باشد',
        }

from .models import DailyExpense

class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient_name', 'patient_phone', 'patient_national_id', 'insurance_type', 'problem_description']
        labels = {
            'patient_name': 'نام و نام خانوادگی',
            'patient_phone': 'شماره همراه',
            'patient_national_id': 'کد ملی',
            'insurance_type': 'نوع بیمه',
            'problem_description': 'شرح مختصر مشکل',
        }
        widgets = {
            'problem_description': forms.Textarea(attrs={'rows': 3}),
        }

class AdHocAppointmentForm(AppointmentBookingForm):
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'placeholder': 'HH:MM'}),
        label="ساعت نوبت"
    )

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['visit_fee_paid', 'service_description', 'payment_method', 'insurance_type']
        labels = {
            'visit_fee_paid': 'مبلغ دریافتی',
            'service_description': 'شرح خدمات',
            'payment_method': 'نحوه پرداخت',
            'insurance_type': 'نوع بیمه',
        }

from .models import DailyExpense, DoctorProfile

class DailyExpenseForm(forms.ModelForm):
    class Meta:
        model = DailyExpense
        fields = ['description', 'amount']
        labels = {
            'description': 'شرح هزینه/پرداخت',
            'amount': 'مبلغ (به تومان)'
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'ایمیل',
        }

class DoctorProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'address', 'phone_number', 'photo', 'biography']
        labels = {
            'specialty': 'تخصص',
            'address': 'آدرس مطب',
            'phone_number': 'شماره تلفن مطب',
            'photo': 'عکس پروفایل',
            'biography': 'بیوگرافی',
        }