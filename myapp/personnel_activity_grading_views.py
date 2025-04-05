from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Personnel, StudentActivity, StudentGrade, PersonnelStudentAssignment, SemesterYear, StudentRecord
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
import xlsxwriter
from io import BytesIO
from django.utils import timezone
from django.conf import settings
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

@login_required(login_url='personnel_login')
def activity_record(request):
    personnel = get_object_or_404(Personnel, user=request.user)
    assignments = PersonnelStudentAssignment.objects.filter(personnel=personnel)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        date = request.POST.get('date')
        activity = request.POST.get('activity')
        merits = request.POST.get('merits', 0)
        demerits = request.POST.get('demerits', 0)
        cdt_sign = request.POST.get('cdt_sign', '')
        fl_sign = request.POST.get('fl_sign', '')
        remarks = request.POST.get('remarks', '')
        
        StudentActivity.objects.create(
            student_id=student_id,
            personnel=personnel,
            date=date,
            activity=activity,
            merits=merits,
            demerits=demerits,
            cdt_sign=cdt_sign,
            fl_sign=fl_sign,
            remarks=remarks
        )
        messages.success(request, 'Activity record added successfully.')
        return redirect('activity_record')
    
    context = {
        'personnel': personnel,
        'assignments': assignments,
    }
    return render(request, 'personnel/activity_record.html', context)

@login_required(login_url='personnel_login')
def compute_grades(request):
    personnel = get_object_or_404(Personnel, user=request.user)
    
    # Get active semesters for the dropdown
    active_semesters = SemesterYear.objects.filter(is_active=True)
    
    if request.method == 'POST':
        period = request.POST.get('period')
        semester_id = request.POST.get('semester_id')
        
        # Validate if period and semester are specified
        if not period or not semester_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'Please specify both the grading period and semester.'
                })
            messages.error(request, 'Please specify both the grading period and semester.')
            return redirect('compute_grades')
        
        # Verify the semester exists and is active
        try:
            semester = SemesterYear.objects.get(id=semester_id, is_active=True)
        except SemesterYear.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': 'The selected semester is not active or does not exist.'
                })
            messages.error(request, 'The selected semester is not active or does not exist.')
            return redirect('compute_grades')
        
        # Process each student's grades
        success_count = 0
        error_messages = []
        
        # Find all student IDs in the form data
        student_ids = []
        for key in request.POST:
            if key.startswith('student_id_'):
                student_id = key.split('_')[-1]
                student_ids.append(student_id)
        
        # If no student IDs found, try to get them from the hidden inputs
        if not student_ids:
            student_ids = request.POST.getlist('student_id')
        
        for student_id in student_ids:
            try:
                # Verify the student belongs to the selected semester
                student = StudentRecord.objects.get(id=student_id, semester_year=semester)
                
                # Get the grade components
                attendance_score = float(request.POST.get(f'attendance_{student_id}', 0))
                military_aptitude = float(request.POST.get(f'military_{student_id}', 0))
                subject_proficiency = float(request.POST.get(f'proficiency_{student_id}', 0))
                
                # Check if grade already exists for this student and period
                grade, created = StudentGrade.objects.get_or_create(
                    student_id=student_id,
                    personnel=personnel,
                    period=period,
                    defaults={
                        'attendance_score': attendance_score,
                        'military_aptitude': military_aptitude,
                        'subject_proficiency': subject_proficiency,
                        'total_grade': 0  # Will be computed below
                    }
                )
                
                if not created:
                    # Update existing grade
                    grade.attendance_score = attendance_score
                    grade.military_aptitude = military_aptitude
                    grade.subject_proficiency = subject_proficiency
                
                # Compute and save the total grade
                grade.total_grade = grade.compute_grade()
                grade.save()
                
                success_count += 1
            except StudentRecord.DoesNotExist:
                error_messages.append(f"Student ID {student_id} not found in the selected semester")
            except ValueError as e:
                error_messages.append(f"Invalid input values for student ID {student_id}: {str(e)}")
            except Exception as e:
                error_messages.append(f"Error processing student ID {student_id}: {str(e)}")
        
        # Prepare response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if success_count > 0:
                return JsonResponse({
                    'success': True, 
                    'message': f'Successfully saved grades for {success_count} students. ' + 
                               (f'Errors: {"; ".join(error_messages)}' if error_messages else '')
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'message': f'Failed to save any grades. Errors: {"; ".join(error_messages)}'
                })
        
        # Regular form submission response
        if success_count > 0:
            messages.success(request, f'Successfully saved grades for {success_count} students.')
            if error_messages:
                messages.warning(request, f'Some grades could not be saved: {"; ".join(error_messages)}')
            return redirect('view_grades')
        else:
            messages.error(request, f'Failed to save any grades. Errors: {"; ".join(error_messages)}')
            return redirect('compute_grades')
    
    context = {
        'personnel': personnel,
        'active_semesters': active_semesters,
    }
    return render(request, 'personnel/compute_grades.html', context)

@login_required(login_url='personnel_login')
def view_grades(request):
    personnel = get_object_or_404(Personnel, user=request.user)
    grades = StudentGrade.objects.filter(personnel=personnel)
    
    context = {
        'personnel': personnel,
        'grades': grades,
    }
    return render(request, 'personnel/view_grades.html', context)

@login_required(login_url='personnel_login')
def get_student_activities(request, student_id):
    activities = StudentActivity.objects.filter(student_id=student_id)
    total_merits = sum(activity.merits for activity in activities)
    total_demerits = sum(activity.demerits for activity in activities)
    military_score = 100 - (total_demerits * 3)  # Deduct 3 points per demerit
    
    return JsonResponse({
        'total_merits': total_merits,
        'total_demerits': total_demerits,
        'military_score': military_score
    })

@login_required(login_url='personnel_login')
def export_grades(request, format):
    personnel = get_object_or_404(Personnel, user=request.user)
    grades = StudentGrade.objects.filter(personnel=personnel).select_related('student')
    
    if format == 'pdf':
        # Create the HttpResponse object with PDF headers
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=20,  # Further reduced margins
            leftMargin=20,
            topMargin=30,
            bottomMargin=30
        )
        elements = []
        
        # Add NOSU logo - Updated path to match Django's static file handling
        logo_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'img', 'LOGO.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path)
            logo.drawHeight = 0.8*inch  # Smaller logo
            logo.drawWidth = 0.8*inch
            logo.hAlign = 'CENTER'
            elements.append(logo)
        
        # Custom styles with smaller fonts
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=14,  # Reduced font size
            spaceAfter=5,
            alignment=1,
            textColor=colors.HexColor('#000080')
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,  # Reduced font size
            spaceAfter=15,
            alignment=1,
            textColor=colors.HexColor('#000080')
        )
        header_info_style = ParagraphStyle(
            'HeaderInfo',
            parent=styles['Normal'],
            fontSize=10,  # Reduced font size
            spaceAfter=20,
            alignment=1,
            textColor=colors.gray
        )
        
        # Add headers with less spacing
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("NEGROS ORIENTAL STATE UNIVERSITY", title_style))
        elements.append(Paragraph("Bayawan-Sta. Catalina Campus", subtitle_style))
        elements.append(Paragraph("Student Grades Report", header_info_style))
        elements.append(Paragraph(
            f"Generated by: {personnel.first_name} {personnel.last_name} | Date: {timezone.now().strftime('%B %d, %Y')}",
            header_info_style
        ))
        elements.append(Spacer(1, 15))
        
        # Create table data with wrapped text
        data = [['Student\nName', 'Period', 'Attendance\n(30%)', 'Military\nAptitude\n(30%)', 
                'Subject\nProficiency\n(40%)', 'Total\nGrade', 'Date']]
        
        for grade in grades:
            # Split long names into multiple lines if needed
            student_name = grade.student.name
            if len(student_name) > 20:  # If name is too long
                words = student_name.split()
                student_name = '\n'.join([' '.join(words[:2]), ' '.join(words[2:])])
            
            data.append([
                student_name,
                Paragraph(grade.period, styles['Normal']),  # Wrap period text
                f"{grade.attendance_score:.2f}",
                f"{grade.military_aptitude:.2f}",
                f"{grade.subject_proficiency:.2f}",
                f"{grade.total_grade:.2f}",
                grade.date_computed.strftime("%m/%d/%Y")
            ])
        
        # Adjust column widths for better text fitting
        col_widths = [140, 100, 70, 70, 70, 60, 70]  # Wider columns for text
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Enhanced table styling for better text display
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Slightly smaller header font
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows styling
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Slightly smaller data font
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f6fa')]),
            
            # Improved padding for all cells
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            
            # Word wrapping
            ('WORDWRAP', (0, 0), (-1, -1), True),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Footer with smaller font
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.gray,
            alignment=1,
            spaceBefore=20
        )
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"Generated from ROTC Management System on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}",
            footer_style
        ))
        
        doc.build(elements)
        
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="NOSU_grades_{timezone.now().strftime("%Y%m%d")}.pdf"'
        response.write(pdf)
        return response
        
    elif format == 'excel':
        # Create the HttpResponse object with Excel headers
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Student Grades')
        
        # Add logo to Excel
        logo_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'img', 'LOGO.png')
        if os.path.exists(logo_path):
            worksheet.insert_image('A1', logo_path, {
                'x_scale': 0.5,
                'y_scale': 0.5,
                'x_offset': 15,
                'y_offset': 5
            })
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#000080'  # Navy blue
        })
        
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#000080'
        })
        
        header_info_format = workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#666666'
        })
        
        # Add titles (adjust row numbers to accommodate logo)
        worksheet.merge_range('C1:G1', 'NEGROS ORIENTAL STATE UNIVERSITY', title_format)
        worksheet.merge_range('C2:G2', 'Bayawan-Sta. Catalina Campus', subtitle_format)
        worksheet.merge_range('C3:G3', 'Student Grades Report', header_info_format)
        worksheet.merge_range('C4:G4', 
            f'Generated by: {personnel.first_name} {personnel.last_name} | Date: {timezone.now().strftime("%B %d, %Y")}',
            header_info_format
        )
        
        # Add some space after the header
        current_row = 6  # Start data after the header
        
        # Adjust Excel cell formatting for better text display
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#2c3e50',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#CCCCCC',
            'font_size': 11,
            'text_wrap': True  # Enable text wrapping
        })
        
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#CCCCCC',
            'text_wrap': True,  # Enable text wrapping
            'font_size': 10
        })
        
        # Add headers with wrapped text
        headers = ['Student Name', 'Period', 'Attendance\n(30%)', 'Military Aptitude\n(30%)', 
                  'Subject Proficiency\n(40%)', 'Total Grade', 'Date']
        
        for col, header in enumerate(headers):
            worksheet.write(current_row, col, header, header_format)
        
        # Set row height for header
        worksheet.set_row(current_row, 30)  # Taller header row
        
        # Add data with adjusted heights
        current_row += 1
        for grade in grades:
            worksheet.write(current_row, 0, grade.student.name, data_format)
            worksheet.write(current_row, 1, grade.period, data_format)
            worksheet.write(current_row, 2, float(grade.attendance_score), data_format)
            worksheet.write(current_row, 3, float(grade.military_aptitude), data_format)
            worksheet.write(current_row, 4, float(grade.subject_proficiency), data_format)
            worksheet.write(current_row, 5, float(grade.total_grade), data_format)
            worksheet.write(current_row, 6, grade.date_computed.strftime("%m/%d/%Y"), data_format)
            
            # Set row height for data rows
            worksheet.set_row(current_row, 25)  # Slightly taller data rows
            current_row += 1
        
        # Adjust column widths
        worksheet.set_column('A:A', 35)  # Student name
        worksheet.set_column('B:B', 25)  # Period
        worksheet.set_column('C:E', 15)  # Scores
        worksheet.set_column('F:F', 12)  # Total Grade
        worksheet.set_column('G:G', 15)  # Date
        
        # Set row height for the header rows
        worksheet.set_row(0, 30)  # Adjust height of first row for logo
        worksheet.set_row(1, 20)
        worksheet.set_row(2, 20)
        worksheet.set_row(3, 20)
        
        workbook.close()
        
        # Create the HttpResponse
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="NOSU_student_grades_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        return response
        
    return HttpResponse('Invalid export format specified.', status=400)

# Add this new API endpoint to fetch students by semester
@login_required(login_url='personnel_login')
def get_semester_students(request, semester_id):
    """API endpoint to get students for a specific semester"""
    try:
        personnel = get_object_or_404(Personnel, user=request.user)
        
        # Get the semester
        semester = get_object_or_404(SemesterYear, id=semester_id)
        
        # Get students assigned to this personnel who are in the selected semester
        assignments = PersonnelStudentAssignment.objects.filter(
            personnel=personnel,
            student__semester_year=semester
        ).select_related('student')
        
        # Format student data for response
        students = []
        for assignment in assignments:
            student = assignment.student
            students.append({
                'id': student.id,
                'name': student.name,
                'student_no': student.student_no,
                'course': student.course,
                'year': student.year,
                'gender': student.gender
            })
        
        return JsonResponse({
            'success': True,
            'students': students
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 