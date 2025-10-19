import datetime
import jdatetime
from django.test import TestCase
from django.urls import reverse
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

        Appointment.objects.create(
            doctor=self.doctor_profile, patient=self.patient_user,
            appointment_datetime=timezone.make_aware(datetime.datetime.combine(yesterday, datetime.time(10, 0))),
            status='COMPLETED', payment_method=2, visit_fee_paid=100000
        )
        DailyExpense.objects.create(doctor=self.doctor_profile, date=yesterday, description="هزینه تست دیروز", amount=-20000)

        Appointment.objects.create(
            doctor=self.doctor_profile, patient=self.patient_user,
            appointment_datetime=timezone.make_aware(datetime.datetime.combine(today, datetime.time(11, 0))),
            status='COMPLETED', payment_method=2, visit_fee_paid=150000
        )
        DailyExpense.objects.create(doctor=self.doctor_profile, date=today, description="هزینه تست امروز", amount=-30000)

        report_url = reverse('booking:financial_report', kwargs={'date': today.strftime('%Y-%m-%d')})
        response = self.client.get(report_url)
        self.assertEqual(response.status_code, 200)

        # Check today's calculations
        self.assertEqual(response.context['total_income'], 150000)
        self.assertEqual(response.context['total_expenses'], 30000)
        self.assertEqual(response.context['net_income'], 120000)
        self.assertIn('نقدی', response.context['income_by_payment_method'])
        self.assertEqual(response.context['income_by_payment_method']['نقدی'], 150000)


        # Test the settle up functionality (based on cash balance)
        response = self.client.post(report_url, {'settle_up': 'true'}, follow=True)
        self.assertEqual(response.status_code, 200)

        # After settling up, the net income should reflect the settlement expense
        self.assertEqual(response.context['net_income'], 0)
        self.assertEqual(response.context['total_expenses'], 150000) # 30000 original + 120000 settlement


        # Check that a settlement expense was created correctly
        settlement_expense = DailyExpense.objects.get(description="تسویه حساب با منشی")
        self.assertEqual(settlement_expense.amount, -120000)