from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models.functions import Length

CharField.register_lookup(Length, 'length')


class MyUser(AbstractUser):
    pass


class Item(models.Model):
    name = models.CharField(max_length=25)

    def _str_(self):
        return self.name

    class Meta:
        verbose_name_plural = 'items'


# rm ./rest/restapi/migrations/ -- !("__init__.py")


class Image(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=False, default='')
    description = models.CharField(max_length=255, blank=True, default='')
    public = models.BooleanField(null=False, default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='images', on_delete=models.CASCADE,
                             db_column="user", blank=True, null=True)
    file = models.ImageField()
    comments = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Comment', blank=True,
                                      related_name="image_comments")
    favourites = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Favourite',
                                        blank=True, related_name="image_favourites")
    votes = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Vote', blank=True, related_name="image_votes")
    reports = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ReportImage', blank=True,
                                     related_name="image_reports")

    def __str__(self):
        return str(self.__class__) + ": " + str(self.id) + ", " + str(self.user)

    class Meta:
        ordering = ['created_at']


class Favourite(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, db_column="image", related_name='favourite_to_image')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             db_column="user", related_name='favourite_to_user')

    class Meta:
        unique_together = ('image', 'user')


class Comment(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, db_column="image", related_name="comment_to_image")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             db_column="user", related_name="comment_to_user")
    created_at = models.DateTimeField(auto_now_add=True)
    comment_text = models.TextField(blank=False)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    class Meta:
        ordering = ['created_at']


class Vote(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, db_column="image", related_name="vote_to_image")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user",
                             related_name="vote_to_user")
    upvote = models.BooleanField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    class Meta:
        unique_together = ('image', 'user')


class ReportImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, db_column="image", related_name="report_to_image")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user",
                             related_name="report_to_user", blank=True, null=True)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
