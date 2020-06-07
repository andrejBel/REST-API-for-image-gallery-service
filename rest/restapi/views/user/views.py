from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, logout
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from ..update_api_view import UpdateAPIView
from ...serializers import UserRegisterSerializer, \
    LoginSerializer, AuthenticationUserSerializer, UserUpdateSerializer, UserSerializer, SocialSerializer

User = get_user_model()


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = ()

    def create_user(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        return user

    @swagger_auto_schema(responses={
        201: AuthenticationUserSerializer(many=True),
        400: "Validation errors",
        401: "Unauthorized",
    },
    )
    def post(self, request, *args, **kwargs):
        '''
        Create a new user, if username is unique and email is unique.
        '''
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = self.create_user(serializer.validated_data)
            user_serialized = AuthenticationUserSerializer(user)
            return Response(data=user_serialized.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeUserDetailView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update_user(self, user, validated_data):
        maybe_password = validated_data.get('new_password', None)
        if maybe_password:
            user.set_password(maybe_password)
        maybe_mail = validated_data.get('email', None)
        if maybe_mail:
            user.mail = user.email
        user.save()

    @swagger_auto_schema(
        responses={
            201: AuthenticationUserSerializer,
            400: "Bad request",
            401: "Unauthorized",
        },
    )
    def put(self, request, *args, **kwargs):
        '''
        Updates user information
        '''
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            self.update_user(user, serializer.validated_data)
            user_serialized = AuthenticationUserSerializer(user)
            return Response(data=user_serialized.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    @swagger_auto_schema(responses={
        200: AuthenticationUserSerializer,
        400: "Validation errors",
        404: "Invalid credentials",
    },
    )
    def post(self, request, *args, **kwargs):
        '''
        Logs user
        '''
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if not user:
                return Response({'error': 'Invalid Credentials'},
                                status=status.HTTP_404_NOT_FOUND)

            user_serialized = AuthenticationUserSerializer(user)
            return Response(data=user_serialized.data,
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: "User logged out",
            401: "Unauthorized",
        },
    )
    def get(self, request, *args, **kwargs):
        '''
        Logout user
        '''
        logout(request)
        return Response({'status': "User logged out"},
                        status=status.HTTP_200_OK)


class UserList(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


from rest_framework import status
from rest_framework.response import Response
from requests.exceptions import HTTPError

from social_django.utils import psa


@swagger_auto_schema(method='post', query_serializer=SocialSerializer,
                     responses={
                         201: AuthenticationUserSerializer,
                         400: "Bad request",
                     },
                     swagger_auto_schema=None)
@api_view(http_method_names=['POST'])
@permission_classes([AllowAny])
@psa()
def social_login_view(request, backend):
    """
    Exchange an OAuth2 access token for one for this site.
    This simply defers the entire OAuth2 process to the front end.
    The front end becomes responsible for handling the entirety of the
    OAuth2 process; we just step in at the end and use the access token
    to populate some user identity.
    For Facebook backend:  POST API_ROOT + /facebook/
    For Google Backend: POST API_ROOT + /google-oauth2/
    """
    serializer = SocialSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        # set up non-field errors key
        # http://www.django-rest-framework.org/api-guide/exceptions/#exception-handling-in-rest-framework-views
        try:
            nfe = settings.NON_FIELD_ERRORS_KEY
        except AttributeError:
            nfe = 'non_field_errors'

        try:
            # this line, plus the psa decorator above, are all that's necessary to
            # get and populate a user object for any properly enabled/configured backend
            # which python-social-auth can handle.
            user = request.backend.do_auth(serializer.validated_data['access_token'])
        except HTTPError as e:
            # An HTTPError bubbled up from the request to the social auth provider.
            # This happens, at least in Google's case, every time you send a malformed
            # or incorrect access key.
            return Response(
                {'errors': {
                    'token': 'Invalid token',
                    'detail': str(e),
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user:
            if user.is_active:
                user_serialized = AuthenticationUserSerializer(user)
                return Response(data=user_serialized.data,
                                status=status.HTTP_201_CREATED)
            else:
                # user is not active; at some point they deleted their account,
                # or were banned by a superuser. They can't just log in with their
                # normal credentials anymore, so they can't log in with social
                # credentials either.
                return Response(
                    {'errors': {nfe: 'This user account is inactive'}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Unfortunately, PSA swallows any information the backend provider
            # generated as to why specifically the authentication failed;
            # this makes it tough to debug except by examining the server logs.
            return Response(
                {'errors': {nfe: "Authentication Failed"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
