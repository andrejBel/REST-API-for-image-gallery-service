import django_filters
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from ..update_api_view import UpdateAPIView
from ...models import Comment, Image
from ...pagination import DefaultPagination
from ...permissions import CommentListViewPermission, CommentDetailViewPermission
from ...serializers import CommentListSerializer, CommentDetailSerializer


# https://django-filter.readthedocs.io/en/master/ref/filterset.html
class CommentFilter(django_filters.FilterSet):
    class Meta:
        model = Comment
        fields = ['created_at', 'comment_text']


class CommentListView(generics.ListAPIView, generics.CreateAPIView):
    permission_classes = [CommentListViewPermission]
    serializer_class = CommentListSerializer
    filterset_class = CommentFilter
    ordering_fields = ['created_at']
    queryset = Comment.objects.all()
    pagination_class = DefaultPagination

    def get_image(self, pk):
        try:
            return Image.objects.get(pk=pk)
        except Image.DoesNotExist:
            raise NotFound(detail="Image not found")

    def get(self, request, pk, *args, **kwargs):
        '''
        Get all comments to image with pk=:id.
        Idf image is public, every user can see comments. Otherwise only owner and admin.
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
            201: CommentListSerializer,
            400: "Bad request",
            403: "Permission denied",
        },
    )
    def post(self, request, pk, *args, **kwargs):
        '''
        Creates an comment to image.
        User has to be authenticated to create a comment.
        Every user can make a comment to public image.
        Only admin and owner can comment private images.
        '''
        image = self.get_image(pk)
        self.check_permission_on_image(request, image)
        serializer = CommentListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user, image=image)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def check_permission_on_image(self, request, obj: Image):
        comment_permission = CommentListViewPermission()
        if not comment_permission.has_permission_on_image(request, obj):
            raise PermissionDenied()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CommentDetailView(UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [CommentDetailViewPermission]
    serializer_class = CommentDetailSerializer
    queryset = Comment.objects.all()

    def get_object(self, pk) -> Comment:
        try:
            return Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            raise NotFound(detail="Comment not found")

    @swagger_auto_schema(
        responses={
            201: CommentDetailSerializer,
            400: "Bad request",
            403: "Permission denied",
            404: "Not found",
        },
    )
    def put(self, request, pk, format=None):
        '''
        Updates a comment with pk=:id
        User has to be authenticated to update a comment.
        Image has to be public and user has to be the owner of comment to edit id.
        Admin and owner of image can update the comment.
        '''
        comment = self.get_object(pk)
        self.check_object_permissions(request, comment)
        serializer = self.get_serializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            204: CommentDetailSerializer,
            403: "Permission denied",
            404: "Not found",
        },
    )
    def delete(self, request, pk, format=None):
        '''
        Deletes a comment with pk=:id
        User has to be authenticated to delete a comment.
        Image has to be public and user has to be the owner of comment to delete id.
        Admin and owner of image can delete the comment.
        '''
        comment: Comment = self.get_object(pk)
        self.check_object_permissions(request, comment)
        comment.delete()
        return Response({"status": "Comment deleted"}, status=status.HTTP_204_NO_CONTENT)
