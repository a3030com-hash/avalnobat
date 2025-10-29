import datetime
import jdatetime
import random
from django.conf import settings
from django.db import transaction, OperationalError
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import DoctorProfile, DoctorAvailability, Appointment, TimeSlotException
from .forms import DoctorAvailabilityForm, AppointmentBookingForm

from django.db.models import Q
import requests

def doctor_list(request):
    """
    نمایش لیست تمام پزشکان با قابلیت جستجو.
    """
    queryset = DoctorProfile.objects.select_related('user', 'specialty').all()
    query = request.GET.get('q')

    if query:
        # Split the search query into individual, non-empty words
        search_terms = [term for term in query.split() if term]
        for term in search_terms:
            # For each term, filter the queryset cumulatively
            queryset = queryset.filter(
                Q(user__first_name__icontains=term) |
                Q(user__last_name__icontains=term) |
                Q(specialty__name__icontains=term) |
                Q(address__icontains=term)
            )

    context = {
        'doctors': queryset,
        'page_title': 'لیست پزشکان'
    }
    return render(request, 'booking/doctor_list.html', context)

def doctor_detail(request, pk):
    """
    نمایش جزئیات یک پزشک خاص و تقویم نوبت‌دهی او بر اساس تاریخ شمسی.
    """
    doctor = get_object_or_404(DoctorProfile.objects.select_related('user', 'specialty'), pk=pk)
    availabilities = doctor.availabilities.filter(is_active=True)

    # محاسبه تقویم برای 45 روز آینده
    today = datetime.date.today()
    jalali_today = jdatetime.date.fromgregorian(date=today)

    # محاسبه روز هفته شمسی برای اولین روز (شنبه=0, یکشنبه=1, ...)
    # jdatetime.weekday(): Sat=0, ..., Fri=6
    # Model: Sat=5, Sun=6, Mon=0, Tue=1, Wed=2, Thu=3, Fri=4
    # We need to map jdatetime weekday to our model's weekday.
    j_to_model_weekday_map = {
        0: 5, # j(Sat)=0 -> m(Sat)=5
        1: 6, # j(Sun)=1 -> m(Sun)=6
        2: 0, # j(Mon)=2 -> m(Mon)=0
        3: 1, # j(Tue)=3 -> m(Tue)=1
        4: 2, # j(Wed)=4 -> m(Wed)=2
        5: 3, # j(Thu)=5 -> m(Thu)=3
        6: 4, # j(Fri)=6 -> m(Fri)=4
    }

    # Calculate the offset for the first day to align the calendar grid correctly
    # The offset is the number of empty cells before the first day (today).
    # jdatetime.weekday(): Sat=0, ..., Fri=6
    calendar_offset = jalali_today.weekday()

    days = []
    for i in range(45):
        current_gregorian_date = today + datetime.timedelta(days=i)
        current_jalali_date = jdatetime.date.fromgregorian(date=current_gregorian_date)

        model_weekday = j_to_model_weekday_map[current_jalali_date.weekday()]
        daily_availabilities = availabilities.filter(day_of_week=model_weekday)

        day_info = {'date': current_gregorian_date, 'status': 'unavailable', 'booked_percentage': 0}

        if daily_availabilities.exists():
            total_capacity = sum(da.visit_count for da in daily_availabilities)
            if total_capacity > 0:
                booked_count = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_datetime__date=current_gregorian_date,
                    status__in=['BOOKED', 'COMPLETED', 'PENDING_PAYMENT']
                ).count()

                booked_percentage = (booked_count / total_capacity) * 100
                day_info['booked_percentage'] = booked_percentage

                if booked_percentage >= 100:
                    day_info['status'] = 'full'
                else:
                    day_info['status'] = 'available'
            else:
                day_info['status'] = 'unavailable' # No capacity

        days.append(day_info)

    context = {
        'doctor': doctor,
        'days': days,
        'calendar_offset': range(calendar_offset),
        'page_title': f'پروفایل دکتر {doctor.user.get_full_name()}'
    }
    return render(request, 'booking/doctor_detail.html', context)

@login_required
def doctor_dashboard(request):
    """
    داشبورد پزشک برای مدیریت زمان‌بندی کاری.
    """
    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        # اگر کاربر پروفایل پزشک نداشته باشد، به صفحه‌ای راهنمایی می‌شود
        # این بخش در آینده می‌تواند کامل‌تر شود
        return redirect('booking:doctor_list')

    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = doctor_profile
            availability.save()
            return redirect('booking:doctor_dashboard')
    else:
        form = DoctorAvailabilityForm()

    availabilities = DoctorAvailability.objects.filter(doctor=doctor_profile).order_by('day_of_week', 'start_time')

    context = {
        'form': form,
        'availabilities': availabilities,
        'page_title': 'داشبورد مدیریت زمان‌بندی'
    }
    return render(request, 'booking/doctor_dashboard.html', context)

@login_required
def edit_availability(request, pk):
    availability = get_object_or_404(DoctorAvailability, pk=pk, doctor=request.user.doctor_profile)
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            return redirect('booking:doctor_dashboard')
    else:
        form = DoctorAvailabilityForm(instance=availability)

    context = {
        'form': form,
        'page_title': 'ویرایش برنامه کاری'
    }
    return render(request, 'booking/edit_availability.html', context)

@login_required
def delete_availability(request, pk):
    availability = get_object_or_404(DoctorAvailability, pk=pk, doctor=request.user.doctor_profile)
    if request.method == 'POST':
        availability.delete()
        return redirect('booking:doctor_dashboard')

    context = {
        'availability': availability,
        'page_title': 'تایید حذف برنامه کاری'
    }
    return render(request, 'booking/delete_availability.html', context)

@login_required
def toggle_availability(request, pk):
    availability = get_object_or_404(DoctorAvailability, pk=pk, doctor=request.user.doctor_profile)
    availability.is_active = not availability.is_active
    availability.save()
    return redirect('booking:doctor_dashboard')

def book_appointment(request, pk, date):
    """
    نمایش تمام ساعات (خالی و پر) و پردازش رزرو نوبت.
    """
    doctor = get_object_or_404(DoctorProfile, pk=pk)
    try:
        jalali_date = jdatetime.datetime.strptime(date, '%Y-%m-%d').date()
        target_date = jalali_date.togregorian()
    except ValueError:
        return redirect('booking:doctor_detail', pk=doctor.pk)

    day_of_week = target_date.weekday()
    availabilities = DoctorAvailability.objects.filter(doctor=doctor, day_of_week=day_of_week, is_active=True)

    if not availabilities.exists():
        return redirect('booking:doctor_detail', pk=doctor.pk)

    all_slots = []
    booked_datetimes = list(Appointment.objects.filter(
        doctor=doctor,
        appointment_datetime__date=target_date,
        status__in=['BOOKED', 'COMPLETED', 'PENDING_PAYMENT']
    ).values_list('appointment_datetime', flat=True))

    canceled_slots = list(TimeSlotException.objects.filter(
        doctor=doctor,
        datetime_slot__date=target_date
    ).values_list('datetime_slot', flat=True))

    for avail in availabilities:
        duration = (datetime.datetime.combine(target_date, avail.end_time) - datetime.datetime.combine(target_date, avail.start_time))
        interval = duration / avail.visit_count if avail.visit_count > 1 else duration
        current_time_naive = datetime.datetime.combine(target_date, avail.start_time)
        for i in range(avail.visit_count):
            current_time_aware = timezone.make_aware(current_time_naive)
            if current_time_aware in booked_datetimes:
                status = 'booked'
            elif current_time_aware in canceled_slots:
                status = 'canceled'
            else:
                status = 'available'
            all_slots.append({'time': current_time_aware, 'status': status})
            current_time_naive += interval

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        selected_slot_str = request.POST.get('selected_slot')

        if form.is_valid() and selected_slot_str:
            appointment_datetime = datetime.datetime.fromisoformat(selected_slot_str)

            try:
                with transaction.atomic():
                    if Appointment.objects.filter(doctor=doctor, appointment_datetime=appointment_datetime, status__in=['BOOKED', 'COMPLETED', 'PENDING_PAYMENT']).exists():
                        raise ValueError("این نوبت لحظاتی پیش رزرو شد.")

                    appointment = form.save(commit=False)
                    appointment.doctor = doctor
                    appointment.appointment_datetime = appointment_datetime
                    appointment.status = 'PENDING_PAYMENT'
                    appointment.save()

                    # --- OTP & SMS Sending Logic ---
                    try:
                        AMOOT_SMS_API_TOKEN=settings.AMOOT_SMS_API_TOKEN
                        AMOOT_SMS_API_URL=settings.AMOOT_SMS_API_URL
                        otp_code = str(random.randint(100000, 999999))
                        request.session['otp_code'] = otp_code
                        request.session['pending_appointment_id'] = appointment.id
                        payload = {
                               'token': AMOOT_SMS_API_TOKEN,
                               'Mobile': appointment.patient_phone,
                               'PatternCodeID':4018,
                               'PatternValues': otp_code,
                            }
                        response=requests.post(AMOOT_SMS_API_URL,data=payload)
                    except requests.exceptions.RequestException as e:
                        print("خطا در ارسال پیامک:", e)
                    return redirect('booking:verify_appointment')

            except ValueError as e:
                error_message = str(e)
                context = {
                    'doctor': doctor, 'date': target_date, 'all_slots': all_slots,
                    'form': form, 'page_title': 'خطا در رزرو نوبت', 'error': error_message
                }
                return render(request, 'booking/book_appointment.html', context)
            except OperationalError as e:
                error_message = "سیستم در حال حاضر قادر به پردازش رزرو شما نیست. لطفاً بعداً دوباره تلاش کنید."
                if "attempt to write a readonly database" in str(e):
                    error_message = "مشکل فنی: پایگاه داده در حالت فقط-خواندنی قرار دارد و امکان ثبت نوبت جدید وجود ندارد. لطفاً به پشتیبانی اطلاع دهید."

                context = {
                    'doctor': doctor, 'date': target_date, 'all_slots': all_slots,
                    'form': form, 'page_title': 'خطای سیستمی', 'error': error_message
                }
                return render(request, 'booking/book_appointment.html', context)
    else:
        form = AppointmentBookingForm()

    context = {
        'doctor': doctor, 'date': target_date, 'all_slots': all_slots,
        'form': form
    }
    return render(request, 'booking/book_appointment.html', context)

from django.contrib.auth import get_user_model
User = get_user_model()

def verify_appointment(request):
    """
تایید شماره همراه با کد یک‌بار مصرف  session.
    """
    pending_appointment_id = request.session.get('pending_appointment_id')
    if not pending_appointment_id:
        return redirect('booking:doctor_list') # اگر نوبتی در حال رزرو نباشد

    appointment = get_object_or_404(Appointment, pk=pending_appointment_id)

    if request.method == 'POST':
        otp_from_user = request.POST.get('otp')
        otp_from_session = request.session.get('otp_code')

        if otp_from_user == otp_from_session:
            # Find or create a patient user with the phone number
            patient_user, created = User.objects.get_or_create(
                username=appointment.patient_phone,
                defaults={
                    'first_name': appointment.patient_name,
                    'user_type': 'PATIENT'
                }
            )
            # Assign the patient to the appointment
            appointment.patient = patient_user
            appointment.save()

            return redirect('booking:payment_page')
        else:
            # کد اشتباه است
            return render(request, 'booking/verify_appointment.html', {'error': 'کد وارد شده صحیح نمی‌باشد.'})

    return render(request, 'booking/verify_appointment.html', {'page_title': 'تأیید نوبت'})

def payment_page(request):
 
    pending_appointment_id = request.session.get('pending_appointment_id')
    if not pending_appointment_id:
        return redirect('booking:doctor_list')

    appointment = get_object_or_404(Appointment, pk=pending_appointment_id)

    # ایجاد درگاه پرداخت زرین‌پال
    merchant_id = "b7861e9d-2b6a-47b5-bac4-acc9e430e827"
    amount = 150000  # مبلغ به ریال
    callback_url = "http://avalnobat.ir/booking/verify_payment/"  # آدرس تأیید پرداخت

    url = "https://payment.zarinpal.com/pg/v4/payment/request.json"
    
    payload = {
        "merchant_id": merchant_id,
        "amount": amount,
        "callback_url": callback_url,
        "description": f"پرداخت نوبت دکتر {appointment.doctor.user.get_full_name()}",
        "metadata": {
            "mobile": appointment.patient_phone,
            "email": getattr(appointment.patient, 'email', '') if hasattr(appointment, 'patient') else ''
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payment_url = None
    authority = None
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()
        
        if response.status_code == 200 and response_data['data']['code'] == 100:
            authority = response_data['data']['authority']
            payment_url = f"https://www.zarinpal.com/pg/StartPay/{authority}"
            
            # ذخیره authority در session برای تأیید بعدی
            request.session['payment_authority'] = authority
            request.session['payment_amount'] = amount
            
            print(f"درگاه پرداخت ایجاد شد: {payment_url}")
        else:
            error_message = response_data['data']['message'] if 'data' in response_data else 'خطای ناشناخته'
            print(f"خطا در ایجاد درگاه: {error_message}")
            
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارتباط با زرین‌پال: {e}")

    context = {
        'appointment': appointment,
        'payment_amount': 150000,  # مبلغ جدید
        'payment_url': payment_url,  # لینک درگاه پرداخت
        'authority': authority,     # کد authority
        'page_title': 'صفحه پرداخت'
    }
    return render(request, 'booking/payment_page.html', context)

def verify_payment(request):
    """
    صفحه تأیید پرداخت پس از بازگشت از درگاه زرین‌پال
    """
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    
    # بازیابی authority از session
    session_authority = request.session.get('payment_authority')
    amount = request.session.get('payment_amount', 100000)
    pending_appointment_id = request.session.get('pending_appointment_id')
    
    if not pending_appointment_id:
        return redirect('booking:doctor_list')
    
    appointment = get_object_or_404(Appointment, pk=pending_appointment_id)
    
    payment_successful = False
    message = ""
    
    if status == 'OK' and authority == session_authority:
        # تأیید پرداخت با زرین‌پال
        merchant_id = "b7861e9d-2b6a-47b5-bac4-acc9e430e827"
        
        verify_url = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
        verify_payload = {
            "merchant_id": merchant_id,
            "amount": amount,
            "authority": authority
        }
        
        try:
            verify_response = requests.post(verify_url, json=verify_payload, timeout=30)
            verify_data = verify_response.json()
            
            if verify_response.status_code == 200:
                if verify_data['data']['code'] == 100:
                    # پرداخت موفق
                    payment_successful = True
                    appointment.is_paid = True
                    appointment.payment_status = 'completed'
                    appointment.save()
                    
                    # پاک کردن session
                    if 'pending_appointment_id' in request.session:
                        del request.session['pending_appointment_id']
                    if 'payment_authority' in request.session:
                        del request.session['payment_authority']
                    if 'payment_amount' in request.session:
                        del request.session['payment_amount']
                    
                    message = "پرداخت با موفقیت انجام شد. نوبت شما ثبت گردید."
                else:
                    message = f"پرداخت ناموفق: {verify_data['data']['message']}"
            else:
                message = "خطا در ارتباط با درگاه پرداخت"
                
        except requests.exceptions.RequestException as e:
            message = f"خطا در تأیید پرداخت: {e}"
    else:
        message = "تراکنش توسط کاربر لغو شد."
    
    context = {
        'payment_successful': payment_successful,
        'message': message,
        'appointment': appointment,
        'page_title': 'نتیجه پرداخت'
    }
    
    return render(request, 'booking/payment_result.html', context)

def initiate_payment(request, appointment_id):
    """
    شروع فرآیند پرداخت و هدایت به درگاه
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    # ذخیره appointment_id در session
    request.session['pending_appointment_id'] = appointment_id
    
    return redirect('booking:payment_page')

def confirm_payment(request):
    """
    پردازش پرداخت شبیه‌سازی شده و نهایی کردن نوبت با استفاده از session.
    """
    pending_appointment_id = request.session.get('pending_appointment_id')
    if not pending_appointment_id:
        return redirect('booking:doctor_list')

    appointment = get_object_or_404(Appointment, pk=pending_appointment_id)

    appointment.status = 'BOOKED'
    appointment.save()

    # Clear the session variable after successful booking
    del request.session['pending_appointment_id']

    context = {
        'appointment': appointment,
        'page_title': 'نوبت شما با موفقیت ثبت شد'
    }
    return render(request, 'booking/confirmation_page.html', context)

from django.contrib.auth import login
from django.http import JsonResponse
from django.forms import modelformset_factory
from .forms import AppointmentUpdateForm, DailyExpenseForm, DoctorRegistrationForm, UserUpdateForm, DoctorProfileUpdateForm
from .models import DailyExpense
from django.db.models import Count

@login_required
def secretary_panel(request, date=None):
    """
    پنل مدیریت منشی (داشبورد).
    """
    if not request.user.user_type == 'DOCTOR':
        return redirect('booking:doctor_list')

    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect('booking:doctor_list')

    if date:
        try:
            current_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.date.today()
    else:
        current_date = datetime.date.today()


    end_date = current_date + datetime.timedelta(days=45)
    availabilities = doctor_profile.availabilities.filter(is_active=True)

    # Optimize appointment counting
    booked_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date__range=[current_date, end_date],
        status__in=['BOOKED', 'COMPLETED', 'PENDING_PAYMENT']
    ).values('appointment_datetime__date').annotate(count=Count('id'))

    booked_counts = {item['appointment_datetime__date']: item['count'] for item in booked_appointments}

    # Get future available days for manual booking
    future_days_info = []
    for i in range(0, 46):  # From today for the next 45 days
        future_date = current_date + datetime.timedelta(days=i)
        daily_availabilities = availabilities.filter(day_of_week=future_date.weekday())

        if daily_availabilities.exists():
            total_capacity = sum(da.visit_count for da in daily_availabilities)
            day_info = {'date': future_date, 'booked_percentage': 0}

            if total_capacity > 0:
                booked_count = booked_counts.get(future_date, 0)
                booked_percentage = (booked_count / total_capacity) * 100
                day_info['booked_percentage'] = booked_percentage

            future_days_info.append(day_info)

    context = {
        'today': current_date,
        'future_days': future_days_info,
        'page_title': 'پنل مدیریت روزانه'
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'booking/secretary_panel_content.html', context)
    return render(request, 'booking/secretary_panel.html', context)


from .models import InsuranceFee

@login_required
def daily_patients(request, date=None):
    """
    نمایش و مدیریت لیست بیماران امروز.
    """
    if not request.user.user_type == 'DOCTOR':
        return redirect('booking:doctor_list')

    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect('booking:doctor_list')

    if date:
        try:
            current_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.date.today()
    else:
        current_date = datetime.date.today()

    AppointmentFormSet = modelformset_factory(Appointment, form=AppointmentUpdateForm, extra=0)

    queryset = Appointment.objects.filter(
        doctor=doctor_profile, appointment_datetime__date=current_date, status='BOOKED'
    ).order_by('appointment_datetime')

    if request.method == 'POST':
        formset = AppointmentFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            appointments = formset.save()
            for appointment in appointments:
                if appointment.visit_fee_paid is not None:
                    InsuranceFee.objects.update_or_create(
                        doctor=doctor_profile,
                        insurance_type=appointment.insurance_type,
                        defaults={'fee': appointment.visit_fee_paid}
                    )
            return redirect('booking:daily_patients', date=date)
    else:
        # Pre-fill visit fee based on insurance
        insurance_fees = {
            fee.insurance_type: fee.fee
            for fee in InsuranceFee.objects.filter(doctor=doctor_profile)
        }
        for appointment in queryset:
            if not appointment.visit_fee_paid:
                appointment.visit_fee_paid = insurance_fees.get(appointment.insurance_type)

        formset = AppointmentFormSet(queryset=queryset)

    context = {
        'formset': formset,
        'today': current_date,
        'page_title': 'لیست بیماران امروز'
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'booking/daily_patients_content.html', context)
    return render(request, 'booking/daily_patients.html', context)


@login_required
def secretary_payments(request, date=None):
    """
    نمایش و ثبت هزینه‌های روزانه منشی.
    """
    if not request.user.user_type == 'DOCTOR':
        return redirect('booking:doctor_list')

    try:
        doctor_profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        return redirect('booking:doctor_list')

    if date:
        try:
            current_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.date.today()
    else:
        current_date = datetime.date.today()


    if request.method == 'POST':
        expense_form = DailyExpenseForm(request.POST)
        if expense_form.is_valid():
            expense = expense_form.save(commit=False)
            expense.doctor = doctor_profile
            expense.date = current_date
            expense.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'description': expense.description,
                    'amount': expense.amount
                })
            return redirect('booking:secretary_payments', date=date)
        elif request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': expense_form.errors})

    expense_form = DailyExpenseForm()
    daily_expenses = DailyExpense.objects.filter(doctor=doctor_profile, date=current_date)

    # Calculate previous day's balance
    yesterday = current_date - datetime.timedelta(days=1)
    previous_cash_income = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date__lte=yesterday,
        payment_method=2,  # نقدی
        visit_fee_paid__isnull=False
    ).aggregate(total=Sum('visit_fee_paid'))['total'] or 0
    previous_expenses_and_payments = DailyExpense.objects.filter(
        doctor=doctor_profile,
        date__lte=yesterday
    ).aggregate(total=Sum('amount'))['total'] or 0
    previous_day_balance = previous_cash_income - previous_expenses_and_payments

  # Calculate today's cash income
    todays_cash_income = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date=current_date,
        payment_method=2,  # نقدی
        visit_fee_paid__isnull=False
    ).aggregate(total=Sum('visit_fee_paid'))['total'] or 0

    # Calculate current secretary cash box balance
    total_cash_income_lte = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date__lte=current_date,
        payment_method=2,  # نقدی
        visit_fee_paid__isnull=False
    ).aggregate(total=Sum('visit_fee_paid'))['total'] or 0

    total_expenses_and_payments = DailyExpense.objects.filter(
        doctor=doctor_profile,
        date__lte=current_date
    ).aggregate(total=Sum('amount'))['total'] or 0

    cash_box_balance = total_cash_income_lte - total_expenses_and_payments

    context = {
        'expense_form': expense_form,
        'daily_expenses': daily_expenses,
        'today': current_date,
        'page_title': 'پرداخت‌های منشی',
        'cash_box_balance': cash_box_balance,
        'previous_day_balance': previous_day_balance,
        'todays_cash_income':todays_cash_income,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'booking/secretary_payments_content.html', context)
    return render(request, 'booking/secretary_payments.html', context)

@login_required
def manage_day(request, date):
    """
    صفحه مدیریت روزانه برای منشی، شامل ثبت نوبت، مسدود کردن و فعال‌سازی نوبت‌ها.
    """
    if not request.user.user_type == 'DOCTOR':
        return redirect('booking:doctor_list')

    doctor_profile = request.user.doctor_profile
    try:
        # The date comes from the URL in Jalali format
        jalali_date = jdatetime.datetime.strptime(date, '%Y-%m-%d').date()
        target_date = jalali_date.togregorian()
    except ValueError:
        return redirect('booking:secretary_panel')

    # --- Logic to calculate and display all time slots ---
    all_slots = []
    booked_datetimes = list(Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date=target_date,
        status__in=['BOOKED', 'COMPLETED', 'PENDING_PAYMENT']
    ).values_list('appointment_datetime', flat=True))

    time_slot_exceptions = TimeSlotException.objects.filter(
        doctor=doctor_profile,
        datetime_slot__date=target_date
    )

    canceled_slots = list(time_slot_exceptions.filter(is_cancellation=True).values_list('datetime_slot', flat=True))
    added_slots = list(time_slot_exceptions.filter(is_cancellation=False).values_list('datetime_slot', flat=True))

    availabilities = DoctorAvailability.objects.filter(
        doctor=doctor_profile,
        day_of_week=target_date.weekday(),
        is_active=True
    )

    for avail in availabilities:
        duration = (datetime.datetime.combine(target_date, avail.end_time) - datetime.datetime.combine(target_date, avail.start_time))
        if avail.visit_count > 0:
            interval = duration / avail.visit_count
            current_time_naive = datetime.datetime.combine(target_date, avail.start_time)
            for i in range(avail.visit_count):
                current_time_aware = timezone.make_aware(current_time_naive)
                status = 'available'
                if current_time_aware in booked_datetimes:
                    status = 'booked'
                elif current_time_aware in canceled_slots:
                    status = 'canceled'

                all_slots.append({'time': current_time_aware, 'status': status})
                current_time_naive += interval

    for added_slot in added_slots:
        if added_slot not in booked_datetimes and added_slot not in canceled_slots:
            all_slots.append({'time': added_slot, 'status': 'available'})

    # Handle POST requests for booking, blocking, or unblocking slots
    if request.method == 'POST':
        action = request.POST.get('action')
        slot_iso = request.POST.get('selected_slot')

        if action and slot_iso:
            slot_datetime = datetime.datetime.fromisoformat(slot_iso)

            if action == 'block':
                TimeSlotException.objects.get_or_create(
                    doctor=doctor_profile,
                    datetime_slot=slot_datetime
                )
                return redirect('booking:manage_day', date=date)

            elif action == 'unblock':
                TimeSlotException.objects.filter(
                    doctor=doctor_profile,
                    datetime_slot=slot_datetime
                ).delete()
                return redirect('booking:manage_day', date=date)

            elif action == 'book':
                form = AppointmentBookingForm(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        # Find or create a patient user
                        patient_user, created = User.objects.get_or_create(
                            username=form.cleaned_data['patient_phone'],
                            defaults={
                                'first_name': form.cleaned_data['patient_name'],
                                'user_type': 'PATIENT'
                            }
                        )
                        # Create the appointment
                        appointment = form.save(commit=False)
                        appointment.doctor = doctor_profile
                        appointment.patient = patient_user
                        appointment.appointment_datetime = slot_datetime
                        appointment.status = 'BOOKED'
                        appointment.save()
                        return redirect('booking:manage_day', date=date)
                # If form is invalid, we will fall through and re-render the page with errors

        elif action == 'add_slot':
            last_slot_time = datetime.time(8, 50) # Default start time if no slots exist
            if all_slots:
                last_slot_time = max(s['time'] for s in all_slots).time()

            new_slot_datetime_naive = datetime.datetime.combine(target_date, last_slot_time) + datetime.timedelta(minutes=10)
            new_slot_datetime_aware = timezone.make_aware(new_slot_datetime_naive)

            TimeSlotException.objects.create(
                doctor=doctor_profile,
                datetime_slot=new_slot_datetime_aware,
                is_cancellation=False # This is an addition, not a cancellation
            )
            return redirect('booking:manage_day', date=date)

    # If the request was a failed POST for booking, use that form, otherwise create a new one
    if request.method == 'POST' and 'form' in locals():
        booking_form = form
    else:
        booking_form = AppointmentBookingForm()

    context = {
        'doctor': doctor_profile,
        'date': target_date,
        'jalali_date_str': date,
        'all_slots': sorted(all_slots, key=lambda x: x['time']),
        'form': booking_form,
        'has_availability': bool(availabilities),
        'page_title': f'مدیریت نوبت‌های روز {date}'
    }
    return render(request, 'booking/manage_day.html', context)


def doctor_signup(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('booking:doctor_dashboard')
    else:
        form = DoctorRegistrationForm()

    context = {
        'form': form,
        'page_title': 'ثبت نام پزشک'
    }
    return render(request, 'booking/signup.html', context)

@login_required
def edit_profile(request):
    if not request.user.user_type == 'DOCTOR':
        return redirect('booking:doctor_list')

    doctor_profile = request.user.doctor_profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = DoctorProfileUpdateForm(request.POST, request.FILES, instance=doctor_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('booking:edit_profile') # Redirect back to the same page to show success
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = DoctorProfileUpdateForm(instance=doctor_profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'page_title': 'ویرایش پروفایل'
    }
    return render(request, 'booking/edit_profile.html', context)

from django.db.models import Sum, Q
from django.urls import reverse

# ... (other code)

@login_required
def edit_expense(request, pk):
    """
    ویرایش یک هزینه یا پرداخت ثبت شده.
    """
    expense = get_object_or_404(DailyExpense, pk=pk, doctor=request.user.doctor_profile)

    if request.method == 'POST':
        form = DailyExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            # Redirect to the secretary_payments page for the date of the expense
            return redirect(reverse('booking:secretary_payments', kwargs={'date': expense.date.strftime('%Y-%m-%d')}))
    else:
        form = DailyExpenseForm(instance=expense)

    context = {
        'form': form,
        'page_title': 'ویرایش هزینه/پرداخت',
        'expense_date': expense.date
    }
    return render(request, 'booking/edit_expense.html', context)

@login_required
def delete_expense(request, pk):
    """
    حذف یک هزینه یا پرداخت ثبت شده.
    """
    expense = get_object_or_404(DailyExpense, pk=pk, doctor=request.user.doctor_profile)
    expense_date_str = expense.date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        expense.delete()
        return redirect(reverse('booking:secretary_payments', kwargs={'date': expense_date_str}))

    context = {
        'expense': expense,
        'page_title': 'تایید حذف',
        'cancel_url': reverse('booking:secretary_payments', kwargs={'date': expense_date_str})
    }
    return render(request, 'booking/delete_expense_confirm.html', context)


@login_required
def financial_report(request, date=None):
    if not request.user.user_type == 'DOCTOR':
        return redirect('booking:doctor_list')

    doctor_profile = request.user.doctor_profile
    if date:
        try:
            current_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.date.today()
    else:
        current_date = datetime.date.today()

    # --- Daily Calculations ---
    todays_appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date=current_date,
        visit_fee_paid__isnull=False
    )
    todays_expenses_queryset = DailyExpense.objects.filter(
        doctor=doctor_profile,
        date=current_date
    )
    total_income = todays_appointments.aggregate(total=Sum('visit_fee_paid'))['total'] or 0
    income_by_payment_method_values = todays_appointments.values('payment_method').annotate(total=Sum('visit_fee_paid'))
    income_by_payment_method_dict = {
        dict(Appointment.PAYMENT_METHOD_CHOICES).get(item['payment_method'], 'نامشخص'): item['total']
        for item in income_by_payment_method_values
    }
    income_by_insurance_values = todays_appointments.values('insurance_type').annotate(total=Sum('visit_fee_paid'), count=Count('id'))
    income_by_insurance_data = {
        dict(Appointment.INSURANCE_CHOICES).get(item['insurance_type'], 'نامشخص'): {
            'total': item['total'],
            'count': item['count']
        }
        for item in income_by_insurance_values
    }
    total_daily_entries = todays_expenses_queryset.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = abs(sum(item.amount for item in todays_expenses_queryset if item.amount > 0))
    total_payments_received = sum(item.amount for item in todays_expenses_queryset if item.amount < 0)
    net_income = total_income - total_daily_entries

    # --- Secretary Cash Box Calculation (Cumulative) ---
    total_cash_income = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_datetime__date__lte=current_date,
        payment_method=2,  # نقدی
        visit_fee_paid__isnull=False
    ).aggregate(total=Sum('visit_fee_paid'))['total'] or 0

    total_expenses_and_payments = DailyExpense.objects.filter(
        doctor=doctor_profile,
        date__lte=current_date
    ).aggregate(total=Sum('amount'))['total'] or 0

    cash_box_balance = total_cash_income - total_expenses_and_payments

    if request.method == 'POST' and 'settle_up' in request.POST:
        if cash_box_balance != 0:
            DailyExpense.objects.create(
                doctor=doctor_profile,
                date=current_date,
                description="تسویه صندوق منشی",
                amount=cash_box_balance
            )
            # Redirect to prevent form resubmission
            return redirect('booking:financial_report', date=current_date.strftime('%Y-%m-%d'))

    context = {
        'today': current_date,
        'page_title': 'گزارش مالی روزانه',
        'total_income': total_income,
        'income_by_payment_method': income_by_payment_method_dict,
        'income_by_insurance': income_by_insurance_data,
        'todays_expenses_queryset': todays_expenses_queryset,
        'total_expenses': total_expenses,
        'total_payments_received': total_payments_received,
        'net_income': net_income,
        'cash_box_balance': cash_box_balance,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'booking/financial_report_content.html', context)
    return render(request, 'booking/financial_report.html', context)