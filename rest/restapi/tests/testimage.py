from typing import Dict

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .dataclasses import ImageTestData, ImageClientData, UserTestData, CommentData, ReportData
from ..models import Image as ModelImage

User = get_user_model()


class ImageTestBase(TestCase):

    def create_user(self, userTestData: UserTestData, superuser: bool = False, authenticate: bool = True) -> User:
        client = APIClient()
        func_to_create_user = User.objects.create_superuser if superuser else User.objects.create_user

        user = func_to_create_user(username=userTestData.username,
                                   password=userTestData.password,
                                   email=userTestData.email)
        if authenticate:
            client.force_authenticate(user=user)  # authentication is tested in other test
        return ImageClientData(user, client)

    def setUp(self):
        self.superuserInfo = self.create_user(UserTestData('admin', '1234pass', 'admin@gmail.com'), True, True)
        self.user1Owner = self.create_user(UserTestData('owner', 'easypass', 'user1@gmail.com'), False, True)
        self.user2Observer = self.create_user(UserTestData('observer', 'easypass', 'user2@gmail.com'), False, True)
        self.anonymousUser = ImageClientData(None, APIClient())

    def image_equal(self, testImage: ImageTestData, returnedDictionary: Dict):
        self.assertEqual(testImage.title, returnedDictionary['title'])
        self.assertEqual(testImage.description, returnedDictionary['description'])
        self.assertEqual(testImage.public, returnedDictionary['public'])


class TestImagesGetImagePost(ImageTestBase):

    def test_image_upload_for_anonymous_user(self):
        image = ImageTestData.create_image_test("through anonym", "lorem ipsum", True, None)
        response = self.anonymousUser.client.post('/images/',
                                                  data=image.to_dict(),
                                                  format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ModelImage.objects.count(), 1)
        lastImage: ModelImage = ModelImage.objects.latest('created_at')
        self.assertEqual(lastImage.user, None)

    def test_image_upload_for_owner_user(self):
        image = ImageTestData.create_image_test("registered", "lorem ipsum", True, self.user1Owner.user)

        response = self.user1Owner.client.post('/images/',
                                               data=image.to_dict(),
                                               format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ModelImage.objects.count(), 1)
        lastImage: ModelImage = ModelImage.objects.latest('created_at')
        self.assertEqual(lastImage.user, self.user1Owner.user)

    def test_image_upload_for_owner_user_private(self):
        image = ImageTestData.create_image_test("registered", "lorem ipsum", True, self.user1Owner.user)

        response = self.user1Owner.client.post('/images/',
                                               data=image.to_dict(),
                                               format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ModelImage.objects.count(), 1)
        lastImage: ModelImage = ModelImage.objects.latest('created_at')
        self.assertEqual(lastImage.user, self.user1Owner.user)

    def test_get_images_for_user(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image_1.create_model_image()

        image_2 = ImageTestData.create_image_test("Image 2", "lorem ipsum", False, self.user1Owner.user)
        image_2.create_model_image()

        image_3 = ImageTestData.create_image_test("Image 3", "lorem ipsum", True, self.user1Owner.user)
        image_3.create_model_image()

        # GET images/ - all public images
        responseOwner = self.user1Owner.client.get('/images/', {"page_size": 10})
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        public_images = responseOwner.data['results']
        self.assertEqual(len(public_images), 2)
        for image in public_images:
            self.assertEqual(image['user'], self.user1Owner.user.id)

        responseAnonymous = self.anonymousUser.client.get('/images/', {"page_size": 10})
        self.assertEqual(responseAnonymous.status_code, status.HTTP_200_OK)
        public_images = responseAnonymous.data['results']
        self.assertEqual(len(public_images), 2)

        responseObserver = self.user2Observer.client.get('/images/', {"page_size": 10})
        self.assertEqual(responseObserver.status_code, status.HTTP_200_OK)
        public_images = responseObserver.data['results']
        self.assertEqual(len(public_images), 2)

        # GET me/images
        responseOwner = self.user1Owner.client.get('/me/images', {"page_size": 10})
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        all_users_images = responseOwner.data['results']
        self.assertEqual(len(all_users_images), 3)
        for image in all_users_images:
            self.assertEqual(image['user'], self.user1Owner.user.id)

        responseObserver = self.user2Observer.client.get('/me/images', {"page_size": 10})
        self.assertEqual(responseObserver.status_code, status.HTTP_200_OK)
        all_users_images = responseObserver.data['results']
        self.assertEqual(len(all_users_images), 0)

        responseAnonymous = self.anonymousUser.client.get('/me/images', {"page_size": 10})
        self.assertEqual(responseAnonymous.status_code, status.HTTP_401_UNAUTHORIZED)


class TestImageDetailView(ImageTestBase):

    def test_image_detail_get(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        image_2 = ImageTestData.create_image_test("Image 2", "lorem ipsum", False, self.user1Owner.user)
        image2InDb = image_2.create_model_image()

        self.assertEqual(ModelImage.objects.all().count(), 2)

        # GET images/:id - get image
        responseOwner = self.user1Owner.client.get('/images/{}'.format(image1InDb.id))
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        self.image_equal(image_1, responseOwner.data)

        responseOwner = self.user1Owner.client.get('/images/{}'.format(image2InDb.id))
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        self.image_equal(image_2, responseOwner.data)

        responseObserver = self.user2Observer.client.get('/images/{}'.format(image1InDb.id))
        self.assertEqual(responseObserver.status_code, status.HTTP_200_OK)
        self.image_equal(image_1, responseObserver.data)

        responseObserver = self.user2Observer.client.get('/images/{}'.format(image2InDb.id))
        self.assertEqual(responseObserver.status_code, status.HTTP_403_FORBIDDEN)

        responseAnonymous = self.anonymousUser.client.get('/images/{}'.format(image1InDb.id))
        self.assertEqual(responseAnonymous.status_code, status.HTTP_200_OK)
        self.image_equal(image_1, responseAnonymous.data)

        responseAnonymous = self.anonymousUser.client.get('/images/{}'.format(image2InDb.id))
        self.assertEqual(responseAnonymous.status_code, status.HTTP_401_UNAUTHORIZED)

        responseAnonymous = self.anonymousUser.client.get('/images/{}'.format(100))
        self.assertEqual(responseAnonymous.status_code, status.HTTP_404_NOT_FOUND)

    def test_image_detail_put(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        self.assertEqual(ModelImage.objects.all().count(), 1)

        # PUT images/:id - put image
        image_1.title = "updated title"
        image_1.description = "updated description"

        responseOwner = self.user1Owner.client.put('/images/{}'.format(image1InDb.id),
                                                   {
                                                       "title": image_1.title,
                                                       "description": image_1.description,
                                                   })
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.image_equal(image_1, responseOwner.data)

        image_1.title = "updated title 2"
        responseOwner = self.user1Owner.client.put('/images/{}'.format(image1InDb.id),
                                                   {
                                                       "title": image_1.title,
                                                   })
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.image_equal(image_1, responseOwner.data)

        # another user should not be able to modify another users image
        responseObserver = self.user2Observer.client.put('/images/{}'.format(image1InDb.id),
                                                         {
                                                             "title": image_1.title,
                                                             "description": image_1.description,
                                                         })
        self.assertEqual(responseObserver.status_code, status.HTTP_403_FORBIDDEN)

    def test_image_detail_delete(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        self.assertEqual(ModelImage.objects.all().count(), 1)

        # DELETE images/:id - put image

        responseObserver = self.user2Observer.client.delete('/images/{}'.format(image1InDb.id))
        self.assertEqual(responseObserver.status_code, status.HTTP_403_FORBIDDEN)

        self.assertIsNotNone(ModelImage.objects.filter(pk=image1InDb.id).first())  # image should be in DB
        responseOwner = self.user1Owner.client.delete('/images/{}'.format(image1InDb.id))
        self.assertEqual(responseOwner.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(ModelImage.objects.filter(pk=image1InDb.id).first())  # image should not be in DB

        responseOwner = self.user1Owner.client.delete('/images/{}'.format(image1InDb.id))
        self.assertEqual(responseOwner.status_code, status.HTTP_404_NOT_FOUND)


class TestImageVote(ImageTestBase):

    def test_image_vote(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        image_2 = ImageTestData.create_image_test("Image 2", "lorem ipsum", True, self.user2Observer.user)
        image2InDb = image_2.create_model_image()

        responseOwner = self.user1Owner.client.put('/images/{}/vote'.format(image1InDb.id), {"type": "up"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image1InDb.vote_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.vote_to_user.count(), 1)

        responseOwner = self.user1Owner.client.put('/images/{}/vote'.format(image2InDb.id), {"type": "down"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.vote_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.vote_to_user.count(), 2)

        # votes again nothing happens
        responseOwner = self.user1Owner.client.put('/images/{}/vote'.format(image2InDb.id), {"type": "down"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.vote_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.vote_to_user.count(), 2)

        responseOwner = self.user1Owner.client.put('/images/{}/vote'.format(image2InDb.id), {"type": "undo"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.vote_to_image.count(), 0)
        self.assertEqual(self.user1Owner.user.vote_to_user.count(), 1)

        responseOwner = self.user1Owner.client.put('/images/{}/vote'.format(image2InDb.id), {"type": "up"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.vote_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.vote_to_user.count(), 2)

        responseObserver = self.user2Observer.client.put('/images/{}/vote'.format(image2InDb.id), {"type": "down"})
        self.assertEqual(responseObserver.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.vote_to_image.count(), 2)
        self.assertEqual(self.user2Observer.user.vote_to_user.count(), 1)

        self.assertEqual(image2InDb.vote_to_image.filter(upvote=True).count(), 1)
        self.assertEqual(image2InDb.vote_to_image.filter(upvote=False).count(), 1)

        # get user voted images
        responseOwner = self.user1Owner.client.get('/me/images/voted')
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        results = responseOwner.data.get('results', None)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)

        responseAnonymous = self.anonymousUser.client.put('/images/{}/vote'.format(image2InDb.id), {"type": "undo"})
        self.assertEqual(responseAnonymous.status_code, status.HTTP_401_UNAUTHORIZED)


class TestImageFavourite(ImageTestBase):

    def test_image_favourite(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        image_2 = ImageTestData.create_image_test("Image 2", "lorem ipsum", True, self.user2Observer.user)
        image2InDb = image_2.create_model_image()

        responseOwner = self.user1Owner.client.put('/images/{}/favourite'.format(image1InDb.id), {"type": "add"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image1InDb.favourite_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.favourite_to_user.count(), 1)

        responseOwner = self.user1Owner.client.put('/images/{}/favourite'.format(image2InDb.id), {"type": "add"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.favourite_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.favourite_to_user.count(), 2)

        # again will not be succesful
        responseOwner = self.user1Owner.client.put('/images/{}/favourite'.format(image2InDb.id), {"type": "add"})
        self.assertEqual(responseOwner.status_code, status.HTTP_400_BAD_REQUEST)

        # remove
        responseOwner = self.user1Owner.client.put('/images/{}/favourite'.format(image2InDb.id), {"type": "remove"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.favourite_to_image.count(), 0)
        self.assertEqual(self.user1Owner.user.favourite_to_user.count(), 1)

        # add again
        responseOwner = self.user1Owner.client.put('/images/{}/favourite'.format(image2InDb.id), {"type": "add"})
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.favourite_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.favourite_to_user.count(), 2)

        responseObserver = self.user2Observer.client.put('/images/{}/favourite'.format(image2InDb.id), {"type": "add"})
        self.assertEqual(responseObserver.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image2InDb.favourite_to_image.count(), 2)
        self.assertEqual(self.user2Observer.user.favourite_to_user.count(), 1)

        self.assertEqual(image2InDb.favourite_to_image.count(), 2)

        # get favourites of user owner
        responseOwner = self.user1Owner.client.get('/me/images/favourites')
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        results = responseOwner.data.get('results', None)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)

        responseAnonymous = self.anonymousUser.client.put('/images/{}/favourite'.format(image2InDb.id), {"type": "add"})
        self.assertEqual(responseAnonymous.status_code, status.HTTP_401_UNAUTHORIZED)


class TestImageReport(ImageTestBase):

    def test_report(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()
        report_data = ReportData("i report this")
        responseObserver = self.user2Observer.client.post('/images/{}/report'.format(image1InDb.id),
                                                          report_data.to_dict())
        self.assertEqual(responseObserver.status_code, status.HTTP_201_CREATED)

        responseOwner = self.user1Owner.client.get('/images/{}/report'.format(image1InDb.id))
        self.assertEqual(responseOwner.status_code, status.HTTP_200_OK)
        results = responseOwner.data.get('results', None)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)

        responseObserver = self.user2Observer.client.get('/images/{}/report'.format(image1InDb.id))
        self.assertEqual(responseObserver.status_code, status.HTTP_403_FORBIDDEN)


class TestImageComment(ImageTestBase):

    def test_comment_add(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        comment1 = CommentData("text comment bla")
        responseOwner = self.user1Owner.client.post('/images/{}/comment'.format(image1InDb.id), comment1.to_dict())
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image1InDb.comment_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.comment_to_user.count(), 1)

        comment2 = CommentData("text comment bla")
        responseObserver = self.user2Observer.client.post('/images/{}/comment'.format(image1InDb.id),
                                                          comment2.to_dict())
        self.assertEqual(responseObserver.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image1InDb.comment_to_image.count(), 2)
        self.assertEqual(self.user2Observer.user.comment_to_user.count(), 1)

    def test_comment_edit(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        comment1 = CommentData("text comment bla")
        responseOwner = self.user1Owner.client.post('/images/{}/comment'.format(image1InDb.id), comment1.to_dict())
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image1InDb.comment_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.comment_to_user.count(), 1)

        commentId = responseOwner.data.get('id', None)
        self.assertIsNotNone(commentId)
        comment1 = CommentData("Edited")
        responseOwner = self.user1Owner.client.put('/comment/{}'.format(commentId), comment1.to_dict())
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)

        responseObserver = self.user2Observer.client.put('/comment/{}'.format(commentId), comment1.to_dict())
        self.assertEqual(responseObserver.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_delete(self):
        image_1 = ImageTestData.create_image_test("Image 1", "lorem ipsum", True, self.user1Owner.user)
        image1InDb = image_1.create_model_image()

        comment1 = CommentData("text comment bla")
        responseOwner = self.user1Owner.client.post('/images/{}/comment'.format(image1InDb.id), comment1.to_dict())
        self.assertEqual(responseOwner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(image1InDb.comment_to_image.count(), 1)
        self.assertEqual(self.user1Owner.user.comment_to_user.count(), 1)

        commentId = responseOwner.data.get('id', None)
        self.assertIsNotNone(commentId)

        responseOwner = self.user1Owner.client.delete('/comment/{}'.format(commentId))
        self.assertEqual(responseOwner.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(image1InDb.comment_to_image.count(), 0)
        self.assertEqual(self.user1Owner.user.comment_to_user.count(), 0)
