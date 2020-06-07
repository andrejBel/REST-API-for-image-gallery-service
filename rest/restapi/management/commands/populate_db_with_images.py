from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()
from ...models import Image

from django.core.files import File
from PIL import Image as pilImage
import tempfile


class Command(BaseCommand):
    help = 'Populates db with basic testing data'

    def create_image(self, title, description, user) -> Image:
        import random
        img = pilImage.new('RGB', (100, 100), color=random.randrange(0, 256))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        img.save(tmp_file)
        # img.name = 'myimage.jpg'

        file = File(tmp_file)
        image = Image(title=title, description=description, user=user, file=None)
        image.save()
        image.file.save(title, file, True)
        return image

    def add_arguments(self, parser):
        parser.add_argument('image_number', type=int, default=10, help='number of images to create')

    def handle(self, *args, **options):
        number_of_images = options['image_number']
        user = User.objects.all().filter(username='test').first()
        if user is not None:
            self.stdout.write(self.style.SUCCESS('Populating'))

            for i in range(0, number_of_images):
                self.create_image('myimage{}.jpg'.format(i), "desc {}".format(i), user)
            self.stdout.write(self.style.SUCCESS('Successfully populated'))
