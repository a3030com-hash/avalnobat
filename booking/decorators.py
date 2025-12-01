from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse

def patient_login_required(function):
    """
    Decorator for views that checks that the user is logged in and is a patient.
    Redirects to the patient login page if necessary.
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'PATIENT':
            return redirect(reverse('booking:patient_login') + '?next=' + request.path)
        return function(request, *args, **kwargs)
    return wrapper

def doctor_required(function):
    return user_passes_test(lambda u: u.is_authenticated and u.user_type == 'DOCTOR')(function)

def secretary_required(function):
    return user_passes_test(lambda u: u.is_authenticated and u.user_type == 'SECRETARY')(function)
