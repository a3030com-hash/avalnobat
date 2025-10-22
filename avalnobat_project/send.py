import os
import django
import sys

# مطمئن شویم مسیر پروژه اضافه شده
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# تنظیمات جنگو
os.environ['DJANGO_SETTINGS_MODULE'] = 'avalnobat_project.settings'

# راه‌اندازی جنگو
try:
    django.setup()
    print("Django setup successful!")
except Exception as e:
    print(f"Django setup failed: {e}")
    exit(1)

# حالا ایمپورت کنیم
try:
    from django.core.mail import send_mail
    from django.conf import settings
    
    print("Email settings:")
    print(f"  Backend: {settings.EMAIL_BACKEND}")
    print(f"  Host: {settings.EMAIL_HOST}")
    print(f"  Port: {settings.EMAIL_PORT}")
    
    # ارسال ایمیل
    result = send_mail(
        'Final Test Email',
        'If you see this, it worked!',
        'info@avalnobat.ir',
        ['a3030.com@gmail.com'],
        fail_silently=False,
    )
    
    print(f"Email send result: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()