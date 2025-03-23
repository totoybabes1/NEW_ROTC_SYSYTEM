from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import StudentRecord, ExcelUpload
from django.contrib import messages
import pandas as pd
from django.utils import timezone
from datetime import timedelta

@login_required
def display_uploaded_tables(request):
    students = StudentRecord.objects.all().order_by('student_no')
    return render(request, 'admin/admin_display_uploaded_tables.html', {'students': students})

@login_required
def upload_excel(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if excel_file and excel_file.name.endswith(('.xlsx', '.xls')):
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                records_created = 0

                # Process each row
                for _, row in df.iterrows():
                    # Extract year and ensure it's a valid year level (1-5)
                    year_value = row.get('Year', 4)  # Default to 4 if not found
                    try:
                        year = int(float(year_value))  # Convert to int, handling potential float values
                        # Ensure year is between 1-5
                        if year < 1 or year > 5:
                            year = 4  # Default to 4 if outside valid range
                    except (ValueError, TypeError):
                        year = 4  # Default to 4 if conversion fails

                    # Get status from Excel or default to 'ACTIVE'
                    status = str(row.get('Status', 'ACTIVE')).upper()
                    if status not in ['ACTIVE', 'INACTIVE']:
                        status = 'ACTIVE'  # Default to ACTIVE if invalid status

                    StudentRecord.objects.create(
                        student_no=str(row['Student No.']),
                        name=row['Name'],
                        gender=row['Gender'],
                        course=row['Course'],
                        year=year,
                        status=status
                    )
                    records_created += 1

                # Update upload record
                upload = ExcelUpload.objects.create(
                    file_name=excel_file.name,
                    total_records=records_created,
                    processed=True
                )

                messages.success(request, f'Successfully uploaded {records_created} records!')
                return redirect('display_uploaded_tables')

            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
        else:
            messages.error(request, 'Please upload only Excel files (.xlsx, .xls)')
    
    uploads = ExcelUpload.objects.all()
    return render(request, 'upload/excel_upload.html', {'uploads': uploads})

@login_required
def delete_excel_upload(request, upload_id):
    if request.method == 'POST':
        try:
            excel_upload = ExcelUpload.objects.get(id=upload_id)
            delete_records = request.POST.get('delete_records') == 'true'
            
            if delete_records:
                # Get the upload date of the excel file to find associated records
                upload_date = excel_upload.upload_date
                # Find all student records created within a minute of this upload
                start_time = upload_date - timedelta(minutes=1)
                end_time = upload_date + timedelta(minutes=1)
                
                # Delete student records created in this time window
                StudentRecord.objects.filter(
                    upload_date__gte=start_time,
                    upload_date__lte=end_time
                ).delete()
                
                messages.success(request, 'Excel file and associated student records deleted successfully!')
            else:
                messages.success(request, 'Excel file deleted successfully!')
            
            # Delete the excel upload record
            excel_upload.delete()
            
        except ExcelUpload.DoesNotExist:
            messages.error(request, 'Excel file not found!')
        except Exception as e:
            messages.error(request, f'Error deleting file: {str(e)}')
    
    return redirect('upload_excel')

@login_required
def edit_student_record(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            student = StudentRecord.objects.get(id=student_id)
            
            # Get form data
            student_no = request.POST.get('student_no', '').strip()
            name = request.POST.get('name', '').strip()
            gender = request.POST.get('gender', '').strip()
            course = request.POST.get('course', '').strip()
            year_value = request.POST.get('year', '4')
            status = request.POST.get('status', 'ACTIVE')
            
            # Validate student number
            if not student_no:
                messages.error(request, 'Student number cannot be empty')
                return redirect('display_uploaded_tables')
            
            # Validate name
            if not name:
                messages.error(request, 'Student name cannot be empty')
                return redirect('display_uploaded_tables')
            
            # Validate gender
            if gender not in ['M', 'F']:
                messages.error(request, 'Gender must be M or F')
                return redirect('display_uploaded_tables')
            
            # Validate course
            if not course:
                course = 'BSCRM'  # Default course
            
            # Validate year
            try:
                year = int(float(year_value))
                if year < 1 or year > 5:
                    year = 2  # Default to year 2 if outside valid range
            except (ValueError, TypeError):
                year = 2  # Default to year 2 if conversion fails
            
            # Update student record
            student.student_no = student_no
            student.name = name
            student.gender = gender
            student.course = course
            student.year = year
            student.status = status
            student.save()
            
            messages.success(request, f'Student record for {name} updated successfully!')
            
        except StudentRecord.DoesNotExist:
            messages.error(request, 'Student record not found!')
        except Exception as e:
            messages.error(request, f'Error updating record: {str(e)}')
    
    return redirect('display_uploaded_tables')

@login_required
def delete_student_record(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            student = StudentRecord.objects.get(id=student_id)
            student_name = student.name  # Store name before deletion for message
            student.delete()
            messages.success(request, f'Student record for {student_name} deleted successfully!')
        except StudentRecord.DoesNotExist:
            messages.error(request, 'Student record not found!')
        except Exception as e:
            messages.error(request, f'Error deleting record: {str(e)}')
    return redirect('display_uploaded_tables')    