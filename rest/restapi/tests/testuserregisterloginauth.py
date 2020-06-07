import base64
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .dataclasses import UserTestData

User = get_user_model()





class AuthenticationTest(TestCase):
    USERNAME = 'testuser'
    PASSWORD = 'heslo123'

    def setUp(self):
        self.client = APIClient()
        self.testUserInfo = UserTestData('testEasy', 'easy1234', 'testEasy@gmail.com')

    def test_user_creation_ok(self):
        response = self.client.post('/register/', data=self.testUserInfo.to_dict())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token = response.data.get("token", None)
        self.assertIsNotNone(token)
        token_in_db = Token.objects.get(user__username=self.testUserInfo.username)
        self.assertIsNotNone(token_in_db)
        created_user_in_db = User.objects.filter(username=self.testUserInfo.username).first()
        self.assertIsNotNone(created_user_in_db)
        return response.data  # returns created usr with token

    def test_user_creation_invalid_password(self):
        user_modifier = deepcopy(self.testUserInfo)
        user_modifier.password = 'short'
        response = self.client.post('/register/', data=user_modifier.to_dict())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_creation_with_same_username(self):
        self.test_user_creation_ok()  # user created
        user_modifier = deepcopy(self.testUserInfo)
        user_modifier.email = 'mail@gmail.com'
        response = self.client.post('/register/', data=user_modifier.to_dict())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_creation_with_same_email(self):
        self.test_user_creation_ok()  # user created
        user_modifier = deepcopy(self.testUserInfo)
        user_modifier.username = 'great_username'
        response = self.client.post('/register/', data=user_modifier.to_dict())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_no_authentication(self):
        self.test_user_creation_ok()  # creates user
        response = self.client.get('/me/images')  # view where user has to be authenticated
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_session_authentication_ok(self):
        self.test_user_creation_ok()  # creates user
        self.client.login(username=self.testUserInfo.username,
                          password=self.testUserInfo.password)  # session authentication with client
        response = self.client.get('/me/images')  # view where user has to be authenticated
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_basic_authentication_ok(self):
        self.test_user_creation_ok()  # creates user
        credentials = base64.b64encode(
            '{}:{}'.format(self.testUserInfo.username, self.testUserInfo.password).encode()).decode('ascii')
        self.client.credentials(
            HTTP_AUTHORIZATION='Basic ' + credentials)
        self.client.login(username=self.testUserInfo.username,
                          password=self.testUserInfo.password)  # session authentication with client
        response = self.client.get('/me/images')  # view where user has to be authenticated
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_token_authentication_ok(self, create_user=True):
        if create_user:
            self.test_user_creation_ok()  # creates user

        response = self.client.post('/login/', data={"username": self.testUserInfo.username,
                                                     "password": self.testUserInfo.password})  # user gets a token if credentials are ok
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # response ok
        token = response.data.get('token', None)  # finds token in response
        self.assertIsNotNone(token)  # be sure token exists
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + token)  # Originally, if we were in postnam we would use attribute in header: AUTHENTICATION = 'Token ' + tokenvalue
        response = self.client.get('/me/images')  # view where user has to be authenticated
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_token_authentication_bad_password(self):
        self.test_user_creation_ok()  # creates user

        response = self.client.post('/login/', data={"username": self.testUserInfo.username,
                                                     "password": 'password'})  # user gets a token if credentials are ok
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # response ok

    def test_user_token_authentication_bad_username(self):
        self.test_user_creation_ok()  # creates user

        response = self.client.post('/login/', data={"username": 'unknown',
                                                     "password": 'password'})  # user gets a token if credentials are ok
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # response ok

    def test_change_password(self):
        self.test_user_token_authentication_ok(True)  # user created and authenticated
        new_password = 'perfect_new_password'
        response = self.client.put('/me/profile', data={
            "current_password": self.testUserInfo.password,
            "new_password": new_password
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.testUserInfo.password = new_password
        self.test_user_token_authentication_ok(False)

    def test_logout_ok(self):
        self.test_user_token_authentication_ok(True)
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_no_authenticated(self):
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
