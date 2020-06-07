from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates admin with name admin and password heslo123'

    def handle(self, *args, **options):
        if not User.objects.all().filter(username='admin'):
            User.objects.create_superuser('admin', 'admin@restapi.com', 'heslo123')
            self.stdout.write(self.style.SUCCESS('Successfully closed admin'))
