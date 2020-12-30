from django.core.management.base import BaseCommand
from dscblog.email import send_alerts


class Command(BaseCommand):
    help = 'Send notifications via email'

    def handle(self, *args, **options):
        self.stdout.write("Sending notifications via email")
        send_alerts()
