from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model 
from .models import OtpToken, Code, CustomUser
from .models import Code
from .models import CompteBancaire
from django.core.validators import RegexValidator


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Enter email address", "class": "form-control"}),
        required=True
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Enter username", "class": "form-control"}),
        required=True
    )
    phone_number = forms.CharField(
        validators=[
            RegexValidator(
                r'^\+?[1-9]\d{1,14}$',  # E.164 format validation
                message="Please enter a valid phone number in E.164 format (e.g. +1234567890)"
            )
        ],
        widget=forms.TextInput(attrs={"placeholder": "Enter phone number", "class": "form-control"})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password", "class": "form-control"}),
        required=True
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password", "class": "form-control"}),
        required=True
    )
    
    class Meta:
        model = get_user_model()
        fields = ('email', 'username', 'phone_number', 'password1', 'password2')



class CodeForm(forms.ModelForm):
    number = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Enter SMS verification Code", "class": "form-control", "maxlength": "6"}),
        required=True
    )

    class Meta:
        model = Code
        fields = ("number",)

    def clean_number(self):
        number = self.cleaned_data.get('number')
        if not number.isdigit() or len(number) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit SMS code.")
        return number



class CompteBancaireForm(forms.ModelForm):
    class Meta:
        model = CompteBancaire
        fields = ['nom', 'prenom', 'profession', 'type_compte', 'solde', 'pays']


class EditForm(forms.ModelForm):
    class Meta:
        model = CompteBancaire
        fields = ['nom', 'prenom', 'profession', 'type_compte', 'solde', 'pays']
