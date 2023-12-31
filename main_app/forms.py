from django import forms
from django.forms.widgets import DateInput, TextInput
from datetime import date
from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs["class"] = "form-control"
            


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[("M", "Male"), ("F", "Female")])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        "password": forms.PasswordInput(),
    }
    profile_pic = forms.ImageField()

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get("instance"):
            instance = kwargs.get("instance").admin.__dict__
            self.fields["password"].required = False
            self.fields["address"].required = False
            self.fields["profile_pic"].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields["password"].widget.attrs[
                    "placeholder"
                ] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data["email"].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError("The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk
            ).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "gender",
            "password",
            "profile_pic",
            "address",
        ]


class EmployeeForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Employee
        fields = CustomUserForm.Meta.fields + ["department"]

    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)

        # Make 'address' and 'profile_pic' fields optional
        self.fields["address"].required = False
        self.fields["profile_pic"].required = False


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class ManagerForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(ManagerForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Manager
        fields = CustomUserForm.Meta.fields + ["department"]


# class DivisionForm(FormSettings):
#     def __init__(self, *args, **kwargs):
#         super(DivisionForm, self).__init__(*args, **kwargs)

#     class Meta:
#         fields = ['name']
#         model = Division


class DepartmentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Department
        fields = ["name"]


# class LeaveReportManagerForm(FormSettings):
#     def __init__(self, *args, **kwargs):
#         super(LeaveReportManagerForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = LeaveReportManager
#         fields = ['date', 'message']
#         widgets = {
#             'date': DateInput(attrs={'type': 'date'}),
#         }


# class FeedbackManagerForm(FormSettings):

#     def __init__(self, *args, **kwargs):
#         super(FeedbackManagerForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = FeedbackManager
#         fields = ['feedback']

class LeaveReportEmployeeForm(FormSettings):
    from_date = forms.DateField(
        label="From",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    to_date = forms.DateField(
        label="To",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = LeaveReportEmployee
        fields = ["from_date", "to_date", "message"]
    
    def clean(self):
        cleaned_data = super().clean()
        from_date = cleaned_data.get("from_date")
        to_date = cleaned_data.get("to_date")

        if from_date and to_date and from_date > to_date:
            raise forms.ValidationError("The 'From' date must be before the 'To' date.")



# class FeedbackEmployeeForm(FormSettings):

#     def __init__(self, *args, **kwargs):
#         super(FeedbackEmployeeForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = FeedbackEmployee
#         fields = ['feedback']


class EmployeeEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(EmployeeEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Employee
        fields = CustomUserForm.Meta.fields


class ManagerEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(ManagerEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Manager
        fields = CustomUserForm.Meta.fields


class EditSalaryForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(EditSalaryForm, self).__init__(*args, **kwargs)

    class Meta:
        model = EmployeeSalary
        fields = ["department", "employee", "base", "ctc"]


class MarkAttendanceForm(FormSettings):
    # def __init__(self, *args, **kwargs):
    #     super(Attendance, self).__init__(*args, **kwargs)
        
    status = forms.ChoiceField(
        choices=[
            choice
            for choice in Attendance.STATUS_CHOICES
            if choice[0] in ["present", "absent"]
        ],
        # widget=forms.RadioSelect,
    )

    class Meta:
        model = Attendance
        fields = ["date","status"]
        widgets = {
            'date': forms.HiddenInput(attrs={'value': date.today().strftime('%Y-%m-%d')}),
        }
        
        # widgets = {
        #     "date": DateInput(attrs={"type": "date"}),
        # }
        
class MarkPresentForm(FormSettings):
    # def __init__(self, *args, **kwargs):
    #     super(Attendance, self).__init__(*args, **kwargs)
        
    # status = forms.ChoiceField(
    #     choices=[
    #         choice
    #         for choice in Attendance.STATUS_CHOICES
    #         if choice[0] in ["present", "absent"]
    #     ],
    #     # widget=forms.RadioSelect,
    # )

    class Meta:
        model = Attendance
        fields = ["date","status"]
        widgets = {
            'date': forms.HiddenInput(attrs={'value': date.today().strftime('%Y-%m-%d')}),
            'status' : forms.HiddenInput(attrs={'value': "present"})
        }
        
        # widgets = {
        #     "date": DateInput(attrs={"type": "date"}),
        # }


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ["name", "date"]
        # Define widgets for specific fields
        widgets = {
            "date": DateInput(attrs={"type": "date"}),
        }
