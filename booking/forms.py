from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from .models import DoctorAvailability, Appointment, Specialty, DoctorProfile, Review

User = get_user_model()

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="نام", widget=forms.TextInput(attrs={'placeholder': 'نام'}))
    last_name = forms.CharField(max_length=30, required=True, label="نام خانوادگی", widget=forms.TextInput(attrs={'placeholder': 'نام خانوادگی'}))
    email = forms.EmailField(required=True, label="ایمیل", widget=forms.EmailInput(attrs={'placeholder': 'ایمیل'}))

    specialty = forms.ModelChoiceField(queryset=Specialty.objects.all(), required=True, label="تخصص")
    address = forms.CharField(max_length=255, required=True, label="آدرس مطب", widget=forms.TextInput(attrs={'placeholder': 'آدرس مطب'}))
    phone_number = forms.CharField(max_length=20, required=True, label="شماره تلفن مطب", widget=forms.TextInput(attrs={'placeholder': 'شماره تلفن مطب'}))
    mobile_number = forms.CharField(max_length=20, required=True, label="شماره موبایل", widget=forms.TextInput(attrs={'placeholder': 'شماره موبایل'}))
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
                mobile_number=self.cleaned_data.get('mobile_number'),
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

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'rating': 'امتیاز',
            'comment': 'نظر',
        }
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['visit_fee_paid', 'service_description', 'payment_method', 'insurance_type', 'problem_description']
        labels = {
            'visit_fee_paid': 'مبلغ دریافتی',
            'service_description': 'شرح خدمات',
            'payment_method': 'نحوه پرداخت',
            'insurance_type': 'نوع بیمه',
            'problem_description': 'شرح حال بیمار',
        }
        widgets = {
            'visit_fee_paid': forms.TextInput(attrs={
                'class': 'number-input',
                'oninput': 'formatNumber(this)',
            }),
        }

from .models import DailyExpense, DoctorProfile

class DailyExpenseForm(forms.ModelForm):
    class Meta:
        model = DailyExpense
        fields = ['description', 'amount']
        labels = {
            'description': 'شرح هزینه/پرداخت',
            'amount': 'مبلغ (به تومان)',
        }
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'مثلاً: هزینه آب و برق'}),
            'amount': forms.TextInput(attrs={
                'class': 'number-input',
                'placeholder': 'مبلغ را به تومان وارد کنید',
                'oninput': 'formatNumber(this)',
                'maxlength': '13',  # Allows for up to 10 digits + 3 commas
            }),
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
        fields = ['specialty', 'address', 'phone_number', 'photo', 'biography', 'visit_fee', 'booking_days', 'secretary_card_number', 'secretary_name', 'secretary_mobile']
        labels = {
            'specialty': 'تخصص',
            'address': 'آدرس مطب',
            'phone_number': 'شماره تلفن مطب',
            'photo': 'عکس پروفایل',
            'biography': 'بیوگرافی',
        }

class SecretarySignUpForm(forms.ModelForm):
    doctor_username = forms.CharField(max_length=150, required=True, label="نام کاربری پزشک")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password')
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_doctor_username(self):
        doctor_username = self.cleaned_data.get('doctor_username')
        try:
            doctor_user = User.objects.get(username=doctor_username, user_type='DOCTOR')
            self.doctor_profile = doctor_user.doctor_profile
        except User.DoesNotExist:
            raise forms.ValidationError("پزشکی با این نام کاربری یافت نشد.")
        return doctor_username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.user_type = 'SECRETARY'
        user.doctor = self.doctor_profile
        if commit:
            user.save()
        return user