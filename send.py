from django.core.mail import send_mail

send_mail(
    'Subject here',
    'Here is the message.',
    'info@avalnobat.ir',
    ['a3030.com@gmail.com'],
    fail_silently=False,
)