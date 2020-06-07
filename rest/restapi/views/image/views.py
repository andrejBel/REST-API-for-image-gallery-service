# Create your views here.
import datetime
import io
import zipfile
from typing import Union

import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ..update_api_view import UpdateAPIView
from ...models import Image, Vote, Favourite, ReportImage
from ...pagination import DefaultPagination
from ...permissions import ImageDetailViewPermission, IsImagePublicOrAdminOrOwnerWithAuthentication, \
    ImageReportListViewPermission
from ...serializers import ImageDetailSerializer, ImageListSerializer, VoteCreateSerializer, FavouriteCreateSerializer, \
    ReportImageListSerilizer

User = get_user_model()


class ImageUserFilter(django_filters.FilterSet):
    created_at = filters.IsoDateTimeFilter()
    visibility = filters.ChoiceFilter(choices=[('public', 'Public'), ('private', 'Private')], null_value='',
                                      method='filter_visibility', help_text="values=(public/ private)",
                                      label="Visibility")

    class Meta:
        model = Image
        fields = {
            'created_at': ['exact', 'year__gt'],
            'description': ['startswith'],
        }

    def filter_visibility(self, queryset, name, value: str):
        if value is not None and len(value) > 0 and value in ('public', 'private'):
            public = value == 'public'
            return queryset.filter(public=public)
        else:
            return queryset


class ImageUserView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Image.objects.all()
    serializer_class = ImageListSerializer
    pagination_class = DefaultPagination
    filterset_class = ImageUserFilter
    ordering_fields = ['created_at']

    @swagger_auto_schema(
        responses={
            # 200 is generated properly with pagination
            401: "Unauthorized",
            403: "Permission denied",
        },
    )
    def get(self, request, *args, **kwargs):
        '''
        Returns all images of authenticated user.
        '''
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class ImageVotedListFilter(django_filters.FilterSet):
    voted = filters.ChoiceFilter(choices=[('up', 'Up'), ('down', 'Down')],
                                 null_value='',
                                 method='filter_voted', help_text="values=(up/down)",
                                 label="Voted images")

    def filter_voted(self, queryset, name, value: str):
        if value is not None and len(value) > 0 and value.lower() in ('up', 'down'):
            value = value.lower()
            value = True if value == 'up' else False
            return queryset.filter(vote_to_image__upvote=value)
        else:
            return queryset


class ImageVoteListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Image.objects.all()
    serializer_class = ImageListSerializer
    pagination_class = DefaultPagination
    filterset_class = ImageVotedListFilter

    # ordering_fields = ['created_at']

    @swagger_auto_schema(
        responses={
            # 200 is generated properly with pagination
            401: "Unauthorized",
            403: "Permission denied",
        },
    )
    def get(self, request, *args, **kwargs):
        '''
        Returns all voted images of authenticated user.
        '''
        return super().get(request, args, kwargs)

    def get_queryset(self):
        return self.queryset.filter(vote_to_image__user=self.request.user)


class ImageFavouriteListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Image.objects.all()
    serializer_class = ImageListSerializer
    pagination_class = DefaultPagination
    ordering_fields = ['created_at']

    @swagger_auto_schema(
        responses={
            # 200 is generated properly with pagination
            401: "Unauthorized",
            403: "Permission denied",
        },
    )
    def get(self, request, *args, **kwargs):
        '''
        Returns all favourites images of authenticated user.
        '''
        return super().get(request, args, kwargs)

    def get_queryset(self):
        return self.queryset.filter(favourite_to_image__user=self.request.user)


class ImageFilter(django_filters.FilterSet):
    description_length = filters.CharFilter('description', lookup_expr='length__lt')
    created_at = filters.IsoDateTimeFilter()
    anonymous = filters.BooleanFilter(field_name='user', lookup_expr="isnull", label="Anonymous user")
    username = filters.CharFilter(field_name='user', method='filter_user', label="Username")
    user_id = filters.CharFilter(field_name='user', lookup_expr='id', label="Username id")
    user_name = filters.CharFilter(field_name='user', lookup_expr='username__istartswith', label="Username name")

    class Meta:
        model = Image
        fields = {
            'created_at': ['date__lte', 'date__gte'],
        }

    def filter_user(self, queryset, name, value: str):
        if value is not None and len(value) > 0:
            if value.lower() == 'me' and self.request.user.is_authenticated:
                value = self.request.user.username

            return queryset.filter(user__username=value)
        else:
            return queryset


class ImageListView(generics.ListAPIView, generics.CreateAPIView):
    parser_classes = (MultiPartParser,)
    queryset = Image.objects.all()
    serializer_class = ImageListSerializer
    pagination_class = DefaultPagination
    filterset_class = ImageFilter
    ordering_fields = ['created_at', 'upvote_count']
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        '''
        Get all public images for anonymous or normal user. <br>
        Get all images for admin user - public and private.
        '''
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={
            200: ImageListSerializer,
            400: "Bad request",
        },
    )
    def post(self, request, *args, **kwargs):
        '''
        Upload an image.
        User can be Anonymous user or normal user.
        Anonymous user can upload only public image.
        '''
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def get_queryset(self):
        if permissions.IsAdminUser().has_permission(self.request, self):
            return self.queryset
        else:
            return self.queryset.filter(public=True)


# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ImageDetailView(generics.RetrieveAPIView, UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [ImageDetailViewPermission]
    serializer_class = ImageDetailSerializer
    parser_class = (FileUploadParser,)
    queryset = Image.objects.all()

    def get_image(self, pk) -> Union[None, Image]:
        try:
            return Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            logger.error("image not found 2!!!")
            raise NotFound(detail="Image not found")

    @swagger_auto_schema(
        responses={
            200: ImageDetailSerializer,
            401: "Unauthorized",
            403: "Permission denied",
            404: "Image not found",
        },
    )
    def get(self, request, pk, format=None):
        """
        Gets image with id=pk.
        If image is private, user has to be the owner of the image or admin.
        Otherwise user can be Anonymous user or normal user.
        """
        image = self.get_image(pk)
        self.check_object_permissions(request, image)
        serializer = ImageDetailSerializer(image)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={
            201: ImageDetailSerializer,
            400: "Bad request",
            401: "Unauthorized",
            403: "Permission denied",
            404: "Image not found",
        },
    )
    def put(self, request, pk, format=None):
        """
        Updates image with :id.
        User has to be the owner of the image or admin to PUT.
        Only admin can PUT image without owner.
        """
        image = self.get_image(pk)
        self.check_object_permissions(request, image)
        serializer = ImageDetailSerializer(image, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            204: "Image deleted",
            403: "Permission denied",
            404: "image not found",
        },
    )
    def delete(self, request, pk, format=None):
        """
        Deletes image with :id.
        User has to be the owner of the image or admin.
        Only admin can DELETE image without owner.
        """
        image = self.get_image(pk)
        self.check_object_permissions(request, image)
        image.file.delete(save=True)
        image.delete()
        return Response({"status": "Image deleted"}, status=status.HTTP_204_NO_CONTENT)


class ImageVoteView(UpdateAPIView):
    permission_classes = [IsImagePublicOrAdminOrOwnerWithAuthentication]
    serializer_class = VoteCreateSerializer
    queryset = Image.objects.all()

    def get_object(self, pk):
        try:
            return Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            raise NotFound(detail="Image not found")

    @swagger_auto_schema(
        responses={
            201: "Message success",
            400: "Bad request",
            401: "Unauthorized",
            403: "Permission denied",
            404: "Image not found",
        },
    )
    def put(self, request, pk, format=None):
        '''
        Method to vote image - up, down or undo vote.
        user has to be authenticated.
        image has to be public so that user can vote it.
        Then, only owner and admin has a right to vote the image.
        '''
        image: Image = self.get_object(pk)
        self.check_object_permissions(request, image)
        user: User = request.user

        user_vote: Vote = image.vote_to_image.filter(user=user).first()

        serializer = VoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['type']

        if action == 'undo' and user_vote is None:
            return Response({'error': 'user has not voted'}, status=status.HTTP_400_BAD_REQUEST)

        if action in ('up', 'down'):
            upvote = action == 'up'
            if user_vote is None:
                user_vote = Vote(image=image, user=user, upvote=upvote)
            else:
                user_vote.upvote = upvote
            user_vote.save()
            return Response({'message': 'user voted the image'}, status=status.HTTP_201_CREATED)
        else:
            user_vote.delete()
            return Response({'message': 'user vote removed'}, status=status.HTTP_201_CREATED)


class UserFavouriteImagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: "HttpResponse with downloadable content",
            403: "Permission denied",
        },
        operation_summary="View for downloadig favourites as *.zip",
        manual_parameters=[openapi.Parameter('name', in_=openapi.IN_QUERY, description='Result name of image',
                                             type=openapi.TYPE_STRING, required=False, default="favourites")]
    )
    def get(self, request, format=None):
        """
        Download favourite images of user in *.zip
        user has to be authenticated.
        """
        user: User = request.user
        user_favourite = Favourite.objects.filter(user=user)

        images = [favourite.image.file for favourite in user_favourite]

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED, False) as zip_file:
            for image in images:
                zip_file.writestr(image.name, image.read())

        zip_filename = request.query_params.get("name", "favourites")
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={}.zip'.format(zip_filename)
        return response


class ImageFavouriteView(UpdateAPIView):
    permission_classes = [IsImagePublicOrAdminOrOwnerWithAuthentication]
    serializer_class = FavouriteCreateSerializer
    queryset = Image.objects.all()

    def get_object(self, pk):
        try:
            return Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            raise NotFound(detail="Image not found")

    @swagger_auto_schema(
        responses={
            201: "Message success",
            400: "Bad request",
            403: "Permission denied",
            404: "Image not found",
        },
    )
    def put(self, request, pk, format=None):
        '''
        Method to add/remove image to users favourite.
        user has to be authenticated.
        image has to be public so that user can add it to favourite.
        Then, only owner and admin has a right to add it to favourites.
        '''
        image: Image = self.get_object(pk)
        self.check_object_permissions(request, image)
        user: User = request.user

        favourite: Favourite = image.favourite_to_image.filter(user=user).first()

        serializer = FavouriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['type']

        if action == 'add' and favourite is not None:
            return Response({'error': 'image already in favourites'}, status=status.HTTP_400_BAD_REQUEST)
        if action == 'remove' and favourite is None:
            return Response({'error': 'image is not in favourites'}, status=status.HTTP_400_BAD_REQUEST)

        if action == 'add':
            favourite = Favourite(image=image, user=user)
            favourite.save()
            return Response({'message': 'image is in favourites'}, status=status.HTTP_201_CREATED)
        else:
            favourite.delete()
            return Response({'message': 'image removed from favourites'}, status=status.HTTP_201_CREATED)


class ImageReportListView(generics.ListAPIView, generics.CreateAPIView):
    permission_classes = [ImageReportListViewPermission]
    serializer_class = ReportImageListSerilizer
    queryset = ReportImage.objects.all().order_by('id')
    pagination_class = DefaultPagination

    def get_image(self, pk):
        try:
            return Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            raise NotFound(detail="Image not found")

    def get(self, request, pk, *args, **kwargs):
        '''
        Get all reports to image with pk=:id.
        Only owner and admin can see reports.
        If owner of image is anonymous, then everyone can see reports.
        '''
        image = self.get_image(pk)
        self.check_permission_on_image(request, image)
        queryset = self.filter_queryset(self.get_queryset().filter(image=image))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={
            201: ReportImageListSerilizer,
            400: "Bad request",
            403: "Permission denied",
        },
    )
    def post(self, request, pk, *args, **kwargs):
        """
        Report an image.
        Everyone has a right to report on public image.
        Only owner and admin can report private image.
        """
        # WORKS only in postman
        image = self.get_image(pk)
        self.check_permission_on_image(request, image)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user, image=image)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def check_permission_on_image(self, request, obj: Image):
        permission = ImageReportListViewPermission()
        if not permission.has_permission_on_image(request, obj):
            raise PermissionDenied()


class ImageTrendingListView(generics.ListAPIView):
    queryset = Image.objects.all()
    serializer_class = ImageListSerializer
    pagination_class = DefaultPagination
    filterset_class = ImageFilter
    ordering_fields = ['created_at', 'upvote_count']
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        '''
        Images sorted by number of votes in last 24 hours. All public images are here.
        '''
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        # self.request.query_params.get(,None)
        date_from = timezone.now() - datetime.timedelta(days=1)
        q = self.queryset \
            .annotate(
            count=Count(
                'vote_to_image__user_id',
                filter=Q(vote_to_image__created_at__gte=date_from),
                distinct=True
            )
        ).order_by('-count')

        return q
