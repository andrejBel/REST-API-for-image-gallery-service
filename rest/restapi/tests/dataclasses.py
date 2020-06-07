import tempfile
from copy import deepcopy, copy

from PIL import Image as PilImage
from django.contrib.auth import get_user_model
from django.core.files import File
from rest_framework.test import APIClient

from ..models import Image as ModelImage

User = get_user_model()


class UserTestData():

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def to_dict(self):
        return deepcopy(self.__dict__)


class ImageClientData():

    def __init__(self, user, client: APIClient):
        self.user = user
        self.client = client


class ImageTestData():

    def __init__(self, title: str, description: str, file, public: bool, user):
        self.title = title
        self.description = description
        self.file = file
        self.public = public
        self.user = user

    @staticmethod
    def create_image_test(title: str, description: str, public: bool, user) -> 'ImageTestData':
        image = PilImage.new('RGB', (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        return ImageTestData(title, description, tmp_file, public, user)

    def create_model_image(self) -> ModelImage:
        file = File(self.file)
        image = ModelImage(title=self.title, description=self.description, user=self.user, public=self.public,
                           file=None)
        image.save()
        image.file.save(self.title, file, True)
        return image

    def to_dict(self):
        dict = copy(self.__dict__)
        dict.pop('user')
        return dict


class CommentData():

    def __init__(self, comment_text):
        self.comment_text = comment_text

    def to_dict(self):
        return deepcopy(self.__dict__)

class ReportData():

    def __init__(self, comment):
        self.comment = comment

    def to_dict(self):
        return deepcopy(self.__dict__)