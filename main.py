# main.py
import os
import sys
import subprocess

def main():
    """اجرای manage.py Django"""
    try:
        # اضافه کردن مسیر پروژه به Python path
        project_path = '/usr/src/app'
        sys.path.insert(0, project_path)
        
        # تنظیم محیط Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avalnobat_project.settings')
        
        print("Starting Django development server...")
        
        # اجرای دستور runserver
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
        
    except ImportError as e:
        print(f"Error importing Django: {e}")
        print("Make sure Django is installed and project structure is correct.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()