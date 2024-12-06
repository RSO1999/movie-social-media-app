
from .models import User
from django import forms
from . import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django import forms
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings


class Registration(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(Registration, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'required': 'True',
            'name': 'username',
            'id': 'username',
            'type': 'text',
            'class': 'form-control',
            'placeholder': 'Username',
            'minlength': '3',
            'maxlength': '20',
        })
        self.fields['email'].widget.attrs.update({
            'required': 'True',
            'name': 'email',
            'id': 'email',
            'type': 'email',
            'class': 'form-control',
            'placeholder': 'name@example.com',
        })
        self.fields['password1'].widget.attrs.update({
            'required': 'True',
            'name': 'password1',
            'id': 'password1',
            'type': 'password',
            'class': 'form-control',
            'placeholder': 'Password',
            'minlength': '4',
        })
        self.fields['password2'].widget.attrs.update({
            'required': 'True',
            'name': 'password2',
            'id': 'password2',
            'type': 'password',
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'minlength': '4',
        })

    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']


class EditProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'required': 'True',
            'name': 'username',
            'id': 'username',
            'type': 'text',
            'class': 'form-control',
            'placeholder': 'Username',
            'minlength': '5',
            'maxlength': '20',
        })
        self.fields['email'].widget.attrs.update({
            'required': 'True',
            'name': 'email',
            'id': 'email',
            'type': 'email',
            'class': 'form-control',
            'placeholder': ''
        })

    class Meta:
        model = User
        fields = ['username', 'email']

    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)


class EditPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(EditPasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'required': 'True',
            'name': 'password1',
            'id': 'password1',
            'type': 'password',
            'class': 'form-control',
            'placeholder': 'Password',
            'minlength': '8',
        }),
        self.fields['new_password2'].widget.attrs.update({
            'required': 'True',
            'name': 'password2',
            'id': 'password2',
            'type': 'password',
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'minlength': '8',
        })

    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']