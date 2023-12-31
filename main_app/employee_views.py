import json
import math
from datetime import datetime, timedelta

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

def employee_apply_leave(request):
    form = LeaveReportEmployeeForm(request.POST or None)
    employee = get_object_or_404(Employee, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportEmployee.objects.filter(employee=employee),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if request.method == 'POST':
            form = LeaveReportEmployeeForm(request.POST)
            if form.is_valid():
                try:
                    employee = get_object_or_404(Employee, admin_id=request.user.id)
                    from_date = form.cleaned_data['from_date']
                    to_date = form.cleaned_data['to_date']
                    message = form.cleaned_data['message']
                    
                    # Generate a list of dates between from_date and to_date
                    date_range = [from_date + timedelta(days=x) for x in range((to_date - from_date).days + 1)]
                    
                    # Create a LeaveReportEmployee object for each date in the range
                    for date in date_range:
                        obj = LeaveReportEmployee(employee=employee, date=date, message=message)
                        obj.save()

                    messages.success(request, "Leave application has been submitted for review")
                    return redirect(reverse('employee_apply_leave'))
                except Exception as e:
                    messages.error(request, "Could not submit leave application")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "employee_template/employee_apply_leave.html", context)



@ csrf_exempt
def employee_home(request):
    employee = get_object_or_404(Employee, admin=request.user)
    form = MarkPresentForm(request.POST or None)
    total_department = Department.objects.all().count()
    
    
    absent_count = Attendance.objects.filter(employee_id=employee.id, status='absent').count()
    present_count = Attendance.objects.filter(employee_id=employee.id, status='present').count()
    holiday_count = Attendance.objects.filter(employee_id=employee.id, status='holiday').count()

    # Count the total number of available attendance records for the employee
    total_attendance_count = Attendance.objects.filter(employee_id=employee.id).count() - holiday_count

    # Calculate the present percentage
    if total_attendance_count != 0:
        absent_percentage = (absent_count / total_attendance_count) * 100
        present_percentage = (present_count / total_attendance_count) * 100
    
    else:
        absent_percentage = 0  # Avoid division by zero
        present_percentage = 0  # Avoid division by zero
    
    current_date = date.today()
    attendance_today = Attendance.objects.filter(employee_id=employee.id, date=current_date).first()

    if attendance_today is not None:
        # Attendance data exists for today
        h3_text = f"{attendance_today.get_status_display()}"
        p_text = "Today"
        form_disabled = True
    else:
        # Attendance data does not exist for today
        h3_text = "Mark Attendance"
        p_text = "Attendance not marked for today"
        form_disabled = False
    
    
    department_name = []
    data_present = []
    data_absent = []
    departments = Department.objects.all()
    context = {
        'employee': employee,
        'absent_percentage': absent_percentage,
        'present_percentage': present_percentage,
        'total_attendance': "Dummy",
        'form': form,
        'total_department': total_department,
        'departments': departments,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': department_name,
        'page_title': 'Employee Homepage',
        'h3_text': h3_text,
        'p_text': p_text,
        'form_disabled': form_disabled,
    }
    return render(request, 'employee_template/home_content.html', context)


# @ csrf_exempt
# def employee_view_attendance(request):
#     employee = get_object_or_404(Employee, admin=request.user)
#     if request.method != 'POST':
#         context = {
#             'departments': Department.objects.all(),
#             'page_title': 'View Attendance'
#         }
#         return render(request, 'employee_template/employee_view_attendance.html', context)
#     else:
#         department_id = request.POST.get('department')
#         start = request.POST.get('start_date')
#         end = request.POST.get('end_date')
#         try:
#             department = get_object_or_404(Department, id=department_id)
#             start_date = datetime.strptime(start, "%Y-%m-%d")
#             end_date = datetime.strptime(end, "%Y-%m-%d")
#             attendance = Attendance.objects.filter(
#                 date__range=(start_date, end_date), department=department)
#             attendance_reports = AttendanceReport.objects.filter(
#                 attendance__in=attendance, employee=employee)
#             json_data = []
#             for report in attendance_reports:
#                 data = {
#                     "date":  str(report.attendance.date),
#                     "status": report.status
#                 }
#                 json_data.append(data)
#             return JsonResponse(json.dumps(json_data), safe=False)
#         except Exception as e:
#             return None

def check_attendance(request,employee ,form,existing_attendance):
    attendance_date = form.cleaned_data['date']
    existing_attendance = Attendance.objects.filter(employee=employee, date=attendance_date).first()
                
    if existing_attendance:
        # Update existing attendance record
        existing_attendance.status = form.cleaned_data['status']
        existing_attendance.save()
        messages.success(request, "Attendance updated")
    else:
        # Create a new attendance record
        obj = form.save(commit=False)
        obj.employee = employee
        obj.save()
        messages.success(request, "Attendance marked")


def employee_mark_attendance(request):
    form = MarkAttendanceForm(request.POST or None)
    employee = get_object_or_404(Employee, admin_id=request.user.id)
    context = {
        'form': form,
        'attendance_history': Attendance.objects.filter(employee=employee),
        'page_title': 'Mark Attendance'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                if form.cleaned_data['date']:
                    attendance_date = form.cleaned_data['date']
                else : 
                    attendance_date = date.today().strftime('%Y-%m-%d')            
                existing_attendance = Attendance.objects.filter(employee=employee, date=attendance_date).first()
                
                check_attendance(request, employee, form, existing_attendance)
                
                return redirect(reverse('employee_mark_attendance'))
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, "Form has errors!")
    return render(request, "employee_template/employee_mark_attendance.html", context)


# def employee_feedback(request):
#     form = FeedbackEmployeeForm(request.POST or None)
#     employee = get_object_or_404(Employee, admin_id=request.user.id)
#     context = {
#         'form': form,
#         # 'feedbacks': FeedbackEmployee.objects.filter(employee=employee),
#         'page_title': 'Employee Feedback'

#     }
#     if request.method == 'POST':
#         if form.is_valid():
#             try:
#                 obj = form.save(commit=False)
#                 obj.employee = employee
#                 obj.save()
#                 messages.success(
#                     request, "Feedback submitted for review")
#                 return redirect(reverse('employee_feedback'))
#             except Exception:
#                 messages.error(request, "Could not Submit!")
#         else:
#             messages.error(request, "Form has errors!")
#     return render(request, "employee_template/employee_feedback.html", context)


def employee_view_profile(request):
    employee = get_object_or_404(Employee, admin=request.user)
    form = EmployeeEditForm(request.POST or None, request.FILES or None,
                           instance=employee)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = employee.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                employee.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('employee_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "employee_template/employee_view_profile.html", context)


@csrf_exempt
def employee_fcmtoken(request):
    token = request.POST.get('token')
    employee_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        employee_user.fcm_token = token
        employee_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def employee_view_notification(request):
    employee = get_object_or_404(Employee, admin=request.user)
    notifications = NotificationEmployee.objects.filter(employee=employee)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "employee_template/employee_view_notification.html", context)


def employee_view_salary(request):
    employee = get_object_or_404(Employee, admin=request.user)
    salarys = EmployeeSalary.objects.filter(employee=employee)
    context = {
        'salarys': salarys,
        'page_title': "View Salary"
    }
    return render(request, "employee_template/employee_view_salary.html", context)

def holiday_list(request):
    holidays = Holiday.objects.all()
    return render(request, 'main_app/holiday_list.html', {'holidays': holidays})
