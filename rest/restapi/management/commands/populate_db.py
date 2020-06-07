from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()
from ...models import Image, Comment, Vote, Favourite

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

    def handle(self, *args, **options):
        if not User.objects.all().filter(username='test').exists():
            self.stdout.write(self.style.SUCCESS('Populating'))
            User.objects.create_user('test', 'test@restapi.com', 'heslo123')
            User.objects.create_user('testnoowner', 'test@restapi.com', 'heslo123')

            user = User.objects.get(username='test')
            admin = User.objects.get(username='admin')

            usernoowner = User.objects.get(username='testnoowner')

            image = self.create_image('myimage1.jpg', "popis", user)

            c = Comment(image=image, user=user, comment_text='text 1')
            c.save()
            c = Comment(image=image, user=user, comment_text='text 3')
            c.save()
            c = Comment(image=image, user=admin, comment_text='text 2')
            c.save()
            c = Comment(image=image, user=usernoowner, comment_text='text 2')
            c.save()

            v = Vote(image=image, user=user, upvote=True)
            v.save()
            v = Vote(image=image, user=admin, upvote=False)
            v.save()
            v = Vote(image=image, user=usernoowner, upvote=False)
            v.save()

            f = Favourite(image=image, user=user)
            f.save()
            f = Favourite(image=image, user=usernoowner)
            f.save()

            image2 = self.create_image('myimage2.jpg', "popis 2", admin)

            c = Comment(image=image2, user=user, comment_text='text 1')
            c.save()
            c = Comment(image=image2, user=user, comment_text='text 3')
            c.save()
            c = Comment(image=image2, user=admin, comment_text='text 2')
            c.save()
            c = Comment(image=image2, user=usernoowner, comment_text='text 2')
            c.save()

            f = Favourite(image=image2, user=user)
            f.save()
            f = Favourite(image=image2, user=usernoowner)
            f.save()

            self.stdout.write(self.style.SUCCESS('Successfully populated'))
