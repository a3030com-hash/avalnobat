import datetime
import jdatetime
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Specialty, DoctorProfile, Appointment, DoctorAvailability, DailyExpense

User = get_user_model()

class BookingAppTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.patient_user = User.objects.create_user(
            username='patient',
            password='password123',
            user_type='PATIENT'
        )
        self.doctor_user = User.objects.create_user(
            username='doctor',
            password='password123',
            first_name='علی',
            last_name='رضایی',
            user_type='DOCTOR'
        )

        # Create Specialty
        self.specialty = Specialty.objects.create(name='قلب و عروق')

        # Create Doctor Profile
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialty=self.specialty,
            address='مشهد - خیابان احمدآباد',
            phone_number='05138400000',
            biography='متخصص قلب با ۱۰ سال سابقه.'
        )

        # Create Doctor Availability
        today_gregorian = datetime.date.today()
        today_jalali = jdatetime.date.fromgregorian(date=today_gregorian)
        j_to_model_weekday_map = { 0: 5, 1: 6, 2: 0, 3: 1, 4: 2, 5: 3, 6: 4 }
        model_weekday = j_to_model_weekday_map[today_jalali.weekday()]

        self.availability = DoctorAvailability.objects.create(
            doctor=self.doctor_profile,
            day_of_week=model_weekday, # Today
            shift='MORNING',
            start_time='09:00:00',
            end_time='12:00:00',
            visit_count=6
        )

    def test_models_creation(self):
        """Test if models are created correctly."""
        self.assertEqual(self.doctor_user.get_full_name(), 'علی رضایی')
        self.assertEqual(self.doctor_profile.specialty.name, 'قلب و عروق')
        self.assertTrue(str(self.doctor_profile).startswith('دکتر'))
        self.assertTrue(str(self.specialty) == 'قلب و عروق')

    def test_doctor_list_view(self):
        """Test the doctor list page."""
        response = self.client.get(reverse('booking:doctor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'دکتر علی رضایی')
        self.assertTemplateUsed(response, 'booking/doctor_list.html')

    def test_doctor_detail_view(self):
        """Test the doctor detail page."""
        response = self.client.get(reverse('booking:doctor_detail', kwargs={'pk': self.doctor_profile.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'متخصص قلب با ۱۰ سال سابقه.')
        self.assertTemplateUsed(response, 'booking/doctor_detail.html')

    def test_doctor_dashboard_view_unauthenticated(self):
        """Test dashboard access for unauthenticated users."""
        response = self.client.get(reverse('booking:doctor_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_doctor_dashboard_view_authenticated(self):
        """Test dashboard access for an authenticated doctor."""
        self.client.login(username='doctor', password='password123')
        response = self.client.get(reverse('booking:doctor_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/doctor_dashboard.html')

    def test_full_booking_flow_for_guest(self):
        """Test the complete booking flow for a guest patient with Jalali date."""
        today_gregorian = datetime.date.today()
        today_jalali_str = jdatetime.date.fromgregorian(date=today_gregorian).strftime('%Y-%m-%d')

        book_url = reverse('booking:book_appointment', kwargs={'pk': self.doctor_profile.pk, 'date': today_jalali_str})
        response = self.client.get(book_url)
        self.assertEqual(response.status_code, 200)

        all_slots = response.context['all_slots']
        available_slots = [s for s in all_slots if s['status'] == 'available']
        self.assertTrue(len(available_slots) > 0)
        selected_slot = available_slots[0]['time'].isoformat()

        response = self.client.post(book_url, {
            'patient_name': 'بیمار تستی', 'patient_phone': '09150000000',
            'patient_national_id': '0000000000', 'insurance_type': 'AZAD',
            'problem_description': 'تست', 'selected_slot': selected_slot
        })

        self.assertEqual(response.status_code, 302)
        appointment = Appointment.objects.first()
        self.assertEqual(appointment.status, 'PENDING_PAYMENT')

        # Manually set the OTP in the session for the test
        session = self.client.session
        session['otp_code'] = '123456'
        session.save()

        verify_url = reverse('booking:verify_appointment')
        response = self.client.post(verify_url, {'otp': '123456'}, follow=True)

        self.assertEqual(response.status_code, 200)
        appointment.refresh_from_db()
        self.assertIsNotNone(appointment.patient)

        confirm_url = reverse('booking:confirm_payment')
        response = self.client.get(confirm_url)

        self.assertEqual(response.status_code, 200)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'BOOKED')

    def test_financial_report(self):
        """Test the financial report for accuracy."""
        self.client.login(username='doctor', password='password123')

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        # Create data for yesterday
        Appointment.objects.create(
            doctor=self.doctor_profile, patient=self.patient_user,
            appointment_datetime=timezone.make_aware(datetime.datetime.combine(yesterday, datetime.time(10, 0))),
            status='COMPLETED', payment_method=2, visit_fee_paid=100000 # Cash
        )
        DailyExpense.objects.create(doctor=self.doctor_profile, date=yesterday, description="هزینه تست دیروز", amount=20000)

        # Create data for today
        Appointment.objects.create(
            doctor=self.doctor_profile, patient=self.patient_user,
            appointment_datetime=timezone.make_aware(datetime.datetime.combine(today, datetime.time(11, 0))),
            status='COMPLETED', payment_method=2, visit_fee_paid=150000 # Cash
        )
        DailyExpense.objects.create(doctor=self.doctor_profile, date=today, description="هزینه تست امروز", amount=30000)

        report_url = reverse('booking:financial_report', kwargs={'period': 'daily', 'date': today.strftime('%Y-%m-%d')})
        response = self.client.get(report_url)
        self.assertEqual(response.status_code, 200)

        # Check today's daily calculations
        self.assertEqual(response.context['total_income'], 150000)
        self.assertEqual(response.context['total_expenses'], 30000)
        self.assertEqual(response.context['net_income'], 120000)

        # Check cumulative cash box balance
        self.assertEqual(response.context['cash_box_balance'], 200000) # (100k+150k) - (20k+30k)

        # Test the settle up functionality
        response = self.client.post(report_url, {'settle_up': 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)

        # After settling up, the cash box balance should be zero
        self.assertEqual(response.context['cash_box_balance'], 0)

        # The day's expenses should now include the settlement amount
        self.assertEqual(response.context['total_expenses'], 230000) # 30,000 original + 200,000 settlement

        # The day's net income reflects the settlement
        self.assertEqual(response.context['net_income'], -80000) # 150,000 income - 230,000 expenses

        # Check that a settlement expense was created correctly
        settlement_expense = DailyExpense.objects.get(description="تسویه صندوق منشی")
        self.assertEqual(settlement_expense.amount, 200000)

    @patch('booking.views.requests.post')
    def test_doctor_signup(self, mock_post):
        """Test the doctor signup process."""
        mock_post.return_value.status_code = 200
        signup_url = reverse('booking:signup')
        form_data = {
            'username': 'newdoctor',
            'password1': 'a_much_stronger_password_123',
            'password2': 'a_much_stronger_password_123',
            'first_name': 'تست',
            'last_name': 'پزشک',
            'email': 'newdoctor@example.com',
            'specialty': self.specialty.pk,
            'address': 'آدرس تستی',
            'phone_number': '0987654321',
            'mobile_number': '09123456789',
            'medical_id': '123456',
        }
        response = self.client.post(signup_url, form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful signup
        self.assertTrue(User.objects.filter(username='newdoctor').exists())
        self.assertTrue(DoctorProfile.objects.filter(user__username='newdoctor').exists())
        doctor_profile = DoctorProfile.objects.get(user__username='newdoctor')
        self.assertEqual(doctor_profile.mobile_number, '09123456789')

    def test_patient_dashboard_access(self):
        """Test patient dashboard access rules."""
        dashboard_url = reverse('booking:patient_dashboard')

        # Test unauthenticated access
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302) # Should redirect to login

        # Test access for a doctor (should be redirected)
        self.client.login(username='doctor', password='password123')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302) # Redirects to doctor_list

        # Test access for a patient
        self.client.login(username='patient', password='password123')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/patient_dashboard.html')

    def test_patient_can_cancel_appointment(self):
        """Test that a patient can cancel a future appointment."""
        self.client.login(username='patient', password='password123')

        # Create a future appointment
        future_date = timezone.now() + datetime.timedelta(days=5)
        future_appointment = Appointment.objects.create(
            doctor=self.doctor_profile,
            patient=self.patient_user,
            appointment_datetime=future_date,
            status='BOOKED'
        )

        # Create a past appointment
        past_date = timezone.now() - datetime.timedelta(days=2)
        past_appointment = Appointment.objects.create(
            doctor=self.doctor_profile,
            patient=self.patient_user,
            appointment_datetime=past_date,
            status='BOOKED'
        )

        # Attempt to cancel the future appointment
        dashboard_url = reverse('booking:patient_dashboard')
        response = self.client.post(dashboard_url, {'appointment_id': future_appointment.id})
        self.assertEqual(response.status_code, 302) # Should redirect

        future_appointment.refresh_from_db()
        self.assertEqual(future_appointment.status, 'CANCELED')

        # Attempt to cancel the past appointment
        response = self.client.post(dashboard_url, {'appointment_id': past_appointment.id})
        self.assertEqual(response.status_code, 302)

        past_appointment.refresh_from_db()
        self.assertEqual(past_appointment.status, 'BOOKED') # Status should not change