from django.contrib.auth.decorators import user_passes_test

def doctor_required(function):
    return user_passes_test(lambda u: u.is_authenticated and u.user_type == 'DOCTOR')(function)

def secretary_required(function):
    return user_passes_test(lambda u: u.is_authenticated and u.user_type == 'SECRETARY')(function)
