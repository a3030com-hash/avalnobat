from django.core.management.base import BaseCommand
from booking.models import CustomUser, DoctorProfile, Specialty, Review, Appointment

class Command(BaseCommand):
    help = 'Creates test data for the booking app.'

    def handle(self, *args, **options):
        # Create a specialty
        specialty, _ = Specialty.objects.get_or_create(name='Cardiology')

        # Create a doctor user
        doctor_user, created = CustomUser.objects.get_or_create(
            username='testdoctor',
            defaults={
                'first_name': 'Test',
                'last_name': 'Doctor',
                'email': 'testdoctor@example.com',
                'user_type': 'DOCTOR'
            }
        )
        if created:
            doctor_user.set_password('password')
            doctor_user.save()

        # Create a doctor profile
        doctor_profile, _ = DoctorProfile.objects.get_or_create(
            user=doctor_user,
            defaults={
                'specialty': specialty,
                'address': '123 Test Street',
                'phone_number': '555-1234',
                'mobile_number': '555-5678',
                'visit_fee': 150000,
            }
        )

        # Create a patient
        patient_user, created = CustomUser.objects.get_or_create(
            username='testpatient',
            defaults={
                'first_name': 'Test',
                'last_name': 'Patient',
                'email': 'testpatient@example.com',
                'user_type': 'PATIENT'
            }
        )
        if created:
            patient_user.set_password('password')
            patient_user.save()

        # Create an appointment
        appointment, _ = Appointment.objects.get_or_create(
            doctor=doctor_profile,
            patient=patient_user,
            defaults={
                'appointment_datetime': '2024-01-01T10:00:00Z',
                'patient_name': 'Test Patient',
                'patient_phone': '555-8765',
                'status': 2, # Completed
            }
        )

        # Create a review
        Review.objects.get_or_create(
            appointment=appointment,
            defaults={
                'rating': 4,
                'comment': 'Great doctor!'
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully created test data.'))
