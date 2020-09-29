from allauth.account.forms import *
from django import forms
from django.contrib.auth import get_user_model


class loginForm(LoginForm):

    def login(self, *args, **kwargs):
        # Add your own processing here.
        # You must return the original result.
        return super(loginForm, self).login(*args, **kwargs)


class signupForm(SignupForm):
    name = forms.CharField(label='Name', max_length=100)
    def save(self, request):
        # Ensure you call the parent class's save.
        # .save() returns a User object.
        print(request)
        user = super(signupForm, self).save(request)
        user.name=self.cleaned_data['name'].strip()
        user.save()
        # Add your own processing here.
        # You must return the original result.
        return user
