from django.core.management.base import BaseCommand
from myapp.models import StudentRecord
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create user accounts for all students in the system'

    def handle(self, *args, **options):
        students = StudentRecord.objects.all()
        created_count = 0
        existing_count = 0
        
        for student in students:
            username = student.student_no
            last_name = student.name.split()[-1]
            password = f"{last_name},"
            
            # Check if user already exists
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=student.name.split()[0] if ' ' in student.name else student.name,
                    last_name=last_name
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created user for student: {student.name}'))
            else:
                existing_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new user accounts'))
        self.stdout.write(self.style.SUCCESS(f'Found {existing_count} existing user accounts')) 