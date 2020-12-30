from dscblog.models import User
from django.core.cache import cache
from django.utils import timezone


class LastVisit:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last visit time after request finished processing.
            User.objects.filter(pk=request.user.pk).update(
                last_visit=timezone.now())
        response = self.get_response(request)
        return response
