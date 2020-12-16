from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.contrib.auth.models import User


@receiver(user_signed_up)
def populate_profile(sociallogin=None, user=None, **kwargs):
    if user != None and sociallogin != None:
        if sociallogin.account.provider == 'google':
            user_data = user.socialaccount_set.filter(
                provider='google')[0].extra_data
            if 'name' in user_data:
                user.name = user_data['name']
            if 'picture' in user_data:
                user.avatar_url = user_data['picture']
            user.save()
