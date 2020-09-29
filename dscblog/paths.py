from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from dscblog.common import to_json


def index(request):
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False}}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    res = render(request, 'index.html', opts)
    return res


def page404(request, exception=None):
    response = render(request, '404.html')
    response.status_code = 404
    return response
