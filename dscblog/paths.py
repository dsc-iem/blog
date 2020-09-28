from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from dscblog.common import to_json


def index(request):
    res = render(request, 'index.html', {'header': {
                 'is_loggedin': False, 'is_empty': False}})
    return res


def page404(request, exception=None):
    response = render(request, '404.html')
    response.status_code = 404
    return response
