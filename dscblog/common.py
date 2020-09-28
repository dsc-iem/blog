from django.http import HttpResponse
import json
from json import JSONEncoder
import datetime
from django.utils.crypto import get_random_string
import django.core.serializers


class DateTimeEncoder(JSONEncoder):
    # Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            return (obj.hour * 60 + obj.minute) * 60 + obj.second


def apiRespond(code, **data):
    res = HttpResponse(json.dumps(data, cls=DateTimeEncoder),
                       content_type="text/json")
    res.status_code = code
    return res


def makecode(length=20):
    return get_random_string(length=length)


def to_json(data):
    return json.dumps(data, cls=DateTimeEncoder)


def dump_datetime(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return (obj.hour * 60 + obj.minute) * 60 + obj.second
    else:
        return obj
