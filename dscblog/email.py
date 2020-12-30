from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
import datetime
from django.utils import timezone
from dscblog.common import makecode, dump_datetime
from dscblog.models import User, Alert
from django.db.models import Q
from django.template.loader import get_template


def send(to, subject, message, html=None):
    try:
        send_mail(
            subject=subject,
            message=message,
            html_message=html,
            from_email='DSC-IEM Blog <'+settings.EMAIL_HOST_USER+'>',
            recipient_list=[to],
            fail_silently=False,
        )
    except Exception as e:
        # print(e)
        return False
    else:
        return True


def get_users_batch(limit=30):
    return User.objects.filter(receive_email_alerts=True, alerts__seen=False).filter(Q(last_alert_email_date__lte=timezone.now(
    )-datetime.timedelta(hours=12)) | Q(last_alert_email_date=None)).order_by('last_alert_email_date')[:limit]


def get_html(context, template='base', user=None):
    context.setdefault('BASE_URL', settings.BASE_URL)
    if user != None:
        context.setdefault('user', user.get_profile_min())
    else:
        context.setdefault('user', None)
    message_template = get_template('emails/'+template+'.html')
    return message_template.render(context)


def get_terms(type, count):
    c = str(count)
    if count == 0:
        return ''
    else:
        s = ''
        ies = 'y'
        if count > 1:
            s = 's'
            ies = 'ies'
        if type == Alert.FOLLOW:
            return c+f' new follower{s}'
        elif type == Alert.NEW_BLOG:
            return c+f' new post{s}'
        elif type == Alert.COMMENT_REPLY:
            return c+f' new repl{ies} on your comment'
        elif type == Alert.COMMENT:
            return c+f' new comment{s}'
        elif type == Alert.REACTION:
            return c+f' new reaction{s}'


def alert_subject(user):
    alerts = Alert.objects.filter(user=user, seen=False)
    sub = '🔔 '
    types_count = 0
    last_type = None
    for typ in Alert.TYPES:
        count = alerts.filter(type=typ[0]).count()
        if count and types_count <= 3:
            if types_count >= 1:
                sub += ', '
            sub += get_terms(typ[0], count)
            types_count += 1
            last_type = typ[0]
    if last_type in [Alert.COMMENT, Alert.REACTION]:
        sub += ' on your blog'
    return sub


def send_alerts():
    users = get_users_batch()
    for user in users:
        msg = Alert.get_new_alerts(user=user)
        heading = 'You have '+str(len(msg))+' new notification'
        if len(msg) > 1:
            heading += 's'
        html = get_html({'alerts': msg, 'heading': heading}, 'alerts', user)
        success = send(to=user.email, subject=alert_subject(
            user), message=heading, html=html)
        if success:
            user.last_alert_email_date = timezone.now()
            user.save()
