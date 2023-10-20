import json
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView

from .forms import *
from .models import *
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Holiday, Attendance
from excel_response import ExcelResponse
from datetime import date, timedelta
import datetime

def view_attendance_excel(request, employee_id):
    employee_id-=1
    employee = get_object_or_404(Employee, id=employee_id)
    attendance_data = Attendance.objects.filter(employee_id=employee_id)
    created_at = employee.admin.created_at.date()
    current_date = date.today()
    all_dates = [created_at + timedelta(days=i) for i in range((current_date - created_at).days + 1)]

    context = {
        'employee': employee,
        'all_dates' : all_dates,
        'attendance_data': attendance_data,
    }

    return render(request, 'ceo_template/employee_attendance.html', context)

def download_attendance_excel(request, employee_id):
    # Fetch the attendance data for the specified employee
    employee = get_object_or_404(Employee, id=employee_id)
    created_at = employee.admin.created_at.date()
    current_date = date.today()
    all_dates = [created_at + timedelta(days=i) for i in range((current_date - created_at).days + 1)]
    attendance_data = Attendance.objects.filter(employee_id=employee_id)

    # Prepare the data in a format suitable for Excel
    data = [
        ['Date', 'Status', 'Created At'],
    ]
    
    for d in all_dates:
        for attendance in attendance_data:
            if d == attendance.date:
                data.append([attendance.date, attendance.status, attendance.created_at])
            else:
                data.append([d, None, ""])
    # Create an ExcelResponse
    return ExcelResponse(request,data, output_name=f'{employee_id}_attendance_{current_date}.xls')


@receiver(post_save, sender=Holiday)
def mark_holiday_attendance(sender, instance, **kwargs):
    date = instance.date
    # department = None  # You can set a default department or choose one
    employees = Employee.objects.all()  # Fetch all employees

    for employee in employees:
        # Check if attendance for the same date and employee exists
        existing_attendance = Attendance.objects.filter(employee=employee, date=date)
        if not existing_attendance:
            # Create a new attendance record
            attendance = Attendance(employee=employee, date=date, status='holiday')
            attendance.save()

def holiday_list(request):
    holidays = Holiday.objects.all()
    return render(request, 'main_app/holiday_list.html', {'holidays': holidays})


def update_attendance_new_employee(employee_id):
    holidays = Holiday.objects.all()
    
    for holiday in holidays:
        date = holiday.date
        
        employee = get_object_or_404(Employee, id=employee_id)
        existing_attendance = Attendance.objects.filter(employee=employee, date=date)
        if not existing_attendance:
            # Create a new attendance record
            attendance = Attendance(employee=employee, date=date, status='holiday')
            attendance.save()

# def add_edit_holiday(request, holiday_id=None):
#     if holiday_id:
#         holiday = Holiday.objects.get(pk=holiday_id)
#     else:
#         holiday = None

#     if request.method == 'POST':
#         form = HolidayForm(request.POST, instance=holiday)
#         if form.is_valid():
#             form.save()
#             return redirect('holiday_list')
#     else:
#         form = HolidayForm(instance=holiday)

#     return render(request, 'ceo_template/add_edit_holiday.html', {'form': form})

def add_edit_holiday(request):
    form = HolidayForm(request.POST or None)
    context = { 
        'form': form,
        'page_title': 'Add Holiday'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            date = form.cleaned_data.get('date')
            try:
                holiday = Holiday()
                holiday.name = name
                holiday.date = date
                holiday.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('holiday_list'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'ceo_template/add_edit_holiday.html', context)

def add_department(request):
    form = DepartmentForm(request.POST or None)
    context = { 
        'form': form,
        'page_title': 'Add Department'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                department = Department()
                department.name = name
                department.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('manage_department'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'ceo_template/add_department_template.html', context)

def admin_home(request):
    total_manager = Manager.objects.all().count()
    total_employees = Employee.objects.all().count()
    departments = Department.objects.all()
    total_department = departments.count()
    attendance_list = Attendance.objects.all()
    total_attendance = attendance_list.count()
    attendance_list = []
    department_list = []
    for department in departments:
        attendance_count = Attendance.objects.all().count()
        department_list.append(department.name[:7])
        attendance_list.append(attendance_count)
    context = {
        'page_title': "Administrative Dashboard",
        # 'total_employees': total_employees,
        # 'total_manager': total_manager,
        # 'total_department': total_department,
        # 'department_list': department_list,
        # 'attendance_list': attendance_list

    }
    return render(request, 'ceo_template/home_content.html', context)

def manage_manager(request):
    allManager = CustomUser.objects.filter(user_type=2)
    context = {
        'allManager': allManager,
        'page_title': 'All Managers'
    }
    return render(request, "ceo_template/manage_manager.html", context)

def add_manager(request):
    form = ManagerForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Manager'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            department = form.cleaned_data.get('department')
            passport = request.FILES.get('profile_pic')
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.manager.department = department
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_manager'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'ceo_template/add_manager_template.html', context)

def add_employee(request):
    if request.method == 'POST':
        employee_form = EmployeeForm(request.POST, request.FILES)
        if employee_form.is_valid():
            first_name = employee_form.cleaned_data.get('first_name')
            last_name = employee_form.cleaned_data.get('last_name')
            email = employee_form.cleaned_data.get('email')
            gender = employee_form.cleaned_data.get('gender')
            password = employee_form.cleaned_data.get('password')
            department = employee_form.cleaned_data.get('department')
            address = employee_form.cleaned_data.get('address', "Selorix Private Limited")

            # Check if 'profile_pic' is provided in the form data
            if 'profile_pic' in request.FILES:
                passport = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(passport.name, passport)
                passport_url = fs.url(filename)
            else:
                # If 'profile_pic' is not provided, set a default profile picture
                fs = FileSystemStorage()
                # filename = fs.save(passport.name, passport)
                passport_url = fs.url("images.png")

            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                if address is not None:
                    user.address = address
                user.employee.department = department
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('manage_employee'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: Form is invalid")
    else:
        employee_form = EmployeeForm()

    context = {'form': employee_form, 'page_title': 'Add Employee'}
    return render(request, 'ceo_template/add_employee_template.html', context)

def manage_employee(request):
    employees = CustomUser.objects.filter(user_type=3)
    context = {
        'employees': employees,
        'page_title': 'All Employees'
    }
    return render(request, "ceo_template/manage_employee.html", context)

def manage_division(request):
    context = {
        'page_title': 'Manage Divisions'
    }
    return render(request, "ceo_template/manage_division.html", context)

def manage_department(request):
    departments = Department.objects.all()
    context = {
        'departments': departments,
        'page_title': 'Manage Departments'
    }
    return render(request, "ceo_template/manage_department.html", context)

def edit_manager(request, manager_id):
    manager = get_object_or_404(Manager, id=manager_id)
    form = ManagerForm(request.POST or None, instance=manager)
    context = {
        'form': form,
        'manager_id': manager_id,
        'page_title': 'Edit Manager'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            # division = form.cleaned_data.get('division')
            department = form.cleaned_data.get('department')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=manager.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                # manager.division = division
                manager.department = department
                user.save()
                manager.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_manager', args=[manager_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please fil form properly")
    else:
        user = CustomUser.objects.get(id=manager_id)
        manager = Manager.objects.get(id=user.id)
        return render(request, "ceo_template/edit_manager_template.html", context)

def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    form = EmployeeForm(request.POST or None, instance=employee)
    context = {
        'form': form,
        'employee_id': employee_id,
        'page_title': 'Edit Employee'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            # division = form.cleaned_data.get('division')
            department = form.cleaned_data.get('department')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=employee.admin.id)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.username = username
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                # employee.division = division
                employee.department = department
                user.save()
                employee.save()
                messages.success(request, "Successfully Updated")
                # return redirect(reverse('edit_employee', args=[employee_id]))
                return redirect(reverse('manage_employee'))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "ceo_template/edit_employee_template.html", context)

def edit_department(request, department_id):
    instance = get_object_or_404(Department, id=department_id)
    form = DepartmentForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'department_id': department_id,
        'page_title': 'Edit Department'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            # division = form.cleaned_data.get('division')
            try:
                department = Department.objects.get(id=department_id)
                department.name = name
                # department.division = division
                department.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_department', args=[department_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'ceo_template/edit_department_template.html', context)

@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)

# @csrf_exempt
# def employee_feedback_message(request):
#     if request.method != 'POST':
#         feedbacks = FeedbackEmployee.objects.all()
#         context = {
#             'feedbacks': feedbacks,
#             'page_title': 'Employee Feedback Messages'
#         }
#         return render(request, 'ceo_template/employee_feedback_template.html', context)
#     else:
#         feedback_id = request.POST.get('id')
#         try:
#             feedback = get_object_or_404(FeedbackEmployee, id=feedback_id)
#             reply = request.POST.get('reply')
#             feedback.reply = reply
#             feedback.save()
#             return HttpResponse(True)
#         except Exception as e:
#             return HttpResponse(False)

# @csrf_exempt
# def manager_feedback_message(request):
#     if request.method != 'POST':
#         feedbacks = FeedbackManager.objects.all()
#         context = {
#             'feedbacks': feedbacks,
#             'page_title': 'Manager Feedback Messages'
#         }
#         return render(request, 'ceo_template/manager_feedback_template.html', context)
#     else:
#         feedback_id = request.POST.get('id')
#         try:
#             feedback = get_object_or_404(FeedbackManager, id=feedback_id)
#             reply = request.POST.get('reply')
#             feedback.reply = reply
#             feedback.save()
#             return HttpResponse(True)
#         except Exception as e:
#             return HttpResponse(False)

# @csrf_exempt
# def view_manager_leave(request):
#     if request.method != 'POST':
#         allLeave = LeaveReportManager.objects.all()
#         context = {
#             'allLeave': allLeave,
#             'page_title': 'Leave Applications From Manager'
#         }
#         return render(request, "ceo_template/manager_leave_view.html", context)
#     else:
#         id = request.POST.get('id')
#         status = request.POST.get('status')
#         if (status == '1'):
#             status = 1
#         else:
#             status = -1
#         try:
#             leave = get_object_or_404(LeaveReportManager, id=id)
#             leave.status = status
#             leave.save()
#             return HttpResponse(True)
#         except Exception as e:
#             return False


@csrf_exempt
def view_employee_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportEmployee.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Employees'
        }
        return render(request, "ceo_template/employee_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportEmployee, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


def admin_view_attendance(request):
    employee = Employee.objects.all()
    employee_data = []
    for emp in employee:
        present_count = Attendance.objects.filter(employee_id=emp.id, status='present').count()
        present_count+= Attendance.objects.filter(employee_id=emp.id, status='holiday').count()

        all_attendance = Attendance.objects.all()
        # Count the total number of available attendance records for the employee
        total_attendance_count = Attendance.objects.filter(employee_id=emp.id).count()

        # Calculate the present percentage
        if total_attendance_count > 0:
            present_percentage = (present_count / total_attendance_count) * 100
        else:
            present_percentage = 0  # Avoid division by zero
            
        employee_data.append({
            'employee': emp,
            'present_percentage': present_percentage,
        })

        
    context = {
        'employees': employee_data,
        'all_data' : all_attendance,
        'page_title': 'View Attendance'
    }

    return render(request, "ceo_template/admin_view_attendance.html", context)

@csrf_exempt
def get_admin_attendance(request):
    department_id = request.POST.get('department')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        department = get_object_or_404(Department, id=department_id)
        attendance = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_reports = AttendanceReport.objects.filter(attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status": str(report.status),
                "name": str(report.employee)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None

def admin_view_profile(request):
    admin = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.admin
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
    return render(request, "ceo_template/admin_view_profile.html", context)


def admin_notify_manager(request):
    manager = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Manager",
        'allManager': manager
    }
    return render(request, "ceo_template/manager_notification.html", context)


def admin_notify_employee(request):
    employee = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Employees",
        'employees': employee
    }
    return render(request, "ceo_template/employee_notification.html", context)


@csrf_exempt
def send_employee_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    employee = get_object_or_404(Employee, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "OfficeOps",
                'body': message,
                'click_action': reverse('employee_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': employee.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationEmployee(employee=employee, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def send_manager_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    manager = get_object_or_404(Manager, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "OfficeOps",
                'body': message,
                'click_action': reverse('manager_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': manager.admin.fcm_token
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationManager(manager=manager, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_manager(request, manager_id):
    manager = get_object_or_404(CustomUser, manager__id=manager_id)
    manager.delete()
    messages.success(request, "Manager deleted successfully!")
    return redirect(reverse('manage_manager'))


def delete_employee(request, employee_id):
    employee = get_object_or_404(CustomUser, employee__id=employee_id)
    employee.delete()
    messages.success(request, "Employee deleted successfully!")
    return redirect(reverse('manage_employee'))


def delete_department(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    department.delete()
    messages.success(request, "Department deleted successfully!")
    return redirect(reverse('manage_department'))


def delete_holiday(request, holiday_id):
    holiday = get_object_or_404(Holiday, id=holiday_id)
    date = holiday.date
    # department = None  # You can set a default department or choose one
    employees = Employee.objects.all()  # Fetch all employees

    for employee in employees:
        # Check if attendance for the same date and employee exists
        Attendance.objects.filter(employee=employee, date=date).delete()
    
    
    
    holiday.delete()
    messages.success(request, "Holiday deleted successfully!")
    return redirect(reverse('holiday_list'))



def manager_add_salary(request):
    # manager = get_object_or_404(Manager, admin=request.user)
    departments = Department.objects.all()
    context = {
        'page_title': 'Salary Upload',
        'departments': departments
    }
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee_list')
            department_id = request.POST.get('department')
            base = request.POST.get('base')
            ctc = request.POST.get('ctc')
            employee = get_object_or_404(Employee, id=employee_id)
            department = get_object_or_404(Department, id=department_id)
            try:
                data = EmployeeSalary.objects.get(
                    employee=employee, department=department)
                data.ctc = ctc
                data.base = base
                data.save()
                messages.success(request, "Salary Updated")
            except:
                salary = EmployeeSalary(employee=employee, department=department, base=base, ctc=ctc)
                salary.save()
                messages.success(request, "Salary Saved")
                return redirect(reverse('get_all_employee_salary'))
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "manager_template/manager_add_salary.html", context)


@csrf_exempt
def fetch_employee_salary(request):
    try:
        department_id = request.POST.get('department')
        employee_id = request.POST.get('employee')
        employee = get_object_or_404(Employee, id=employee_id)
        department = get_object_or_404(Department, id=department_id)
        salary = EmployeeSalary.objects.get(employee=employee, department=department)
        salary_data = {
            'ctc': salary.ctc,
            'base': salary.base
        }
        return HttpResponse(json.dumps(salary_data))
    except Exception as e:
        return HttpResponse('False')

def get_all_employee_salary(request):
    # employee = get_object_or_404(Employee, admin=request.user)
    salarys = EmployeeSalary.objects.all()
    context = {
        'salarys': salarys,
        'page_title': "All Salary"
    }
    return render(request, "ceo_template/manage_employee_salary.html", context)
