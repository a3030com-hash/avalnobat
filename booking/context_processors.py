def patient_session_processor(request):
    patient_phone = request.session.get('patient_phone')
    if patient_phone:
        return {
            'is_patient_logged_in': True,
            'patient_phone': patient_phone
        }
    return {
        'is_patient_logged_in': False
    }
