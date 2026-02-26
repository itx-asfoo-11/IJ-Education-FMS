from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from .models import CustomUser, Student, ClassFee, FeeRecord, FeePayment


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)


class SecurityAnswerForm(forms.Form):
    username = forms.CharField()
    answer = forms.CharField(widget=forms.PasswordInput)


class CustomUserCreationForm(UserCreationForm):
    security_answer = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Security answer will be hashed.")
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    user_permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'security_question', 'security_answer', 'groups', 'user_permissions')

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_answer = self.cleaned_data.get('security_answer')
        if raw_answer:
            user.set_security_answer(raw_answer)
        if commit:
            user.save()
            self.save_m2m() # Required for groups/permissions
        return user


class CustomUserUpdateForm(UserChangeForm):
    password = None  # Use password change views for actual resets
    security_answer = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank to keep current answer.")
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    user_permissions = forms.ModelMultipleChoiceField(queryset=Permission.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'security_question', 'security_answer', 'groups', 'user_permissions', 'is_active', 'is_staff')

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_answer = self.cleaned_data.get('security_answer')
        if raw_answer:
            user.set_security_answer(raw_answer)
        if commit:
            user.save()
            self.save_m2m()
        return user


class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = Group
        fields = ('name', 'permissions')


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ('photo', 'manual_fee', 'created_at') # Removal requested
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ClassFeeForm(forms.ModelForm):
    class Meta:
        model = ClassFee
        fields = '__all__'


class FeeRecordForm(forms.ModelForm):
    class Meta:
        model = FeeRecord
        exclude = ('month', 'due_date') # Automation only
        widgets = {
            'submission_date': forms.DateInput(attrs={'type': 'date'}),
        }


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
