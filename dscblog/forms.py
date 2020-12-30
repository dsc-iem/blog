from allauth.account.forms import *
from django import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from dscblog.models import User, Blog


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
        user.name = self.cleaned_data['name'].strip()
        user.save()
        # Add your own processing here.
        # You must return the original result.
        return user


class UserSettingsForm(ModelForm):
    avatar_url = forms.CharField(required=False, label='Picture URL')
    bio = forms.CharField(required=False, label='Bio', widget=forms.Textarea)
    receive_email_alerts = forms.BooleanField(required=False, label='Receive notifications by Email', widget=forms.CheckboxInput)
    receive_newsletters = forms.BooleanField(required=False, label='Receive newsletters', widget=forms.CheckboxInput)

    class Meta:
        model = User
        fields = ['name', 'username', 'avatar_url', 'bio',
                  'receive_email_alerts', 'receive_newsletters']
        labels = {
            'name': 'Full name'
        }
