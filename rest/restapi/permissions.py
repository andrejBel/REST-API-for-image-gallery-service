# Anonymous user
# Normal user -> not owner
# Owner user == Admin user

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny

from .models import Image, Comment, ReportImage


class ImageDetailViewPermission(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj: Image):
        # if user is owner or admin -> ewerything
        if request.method == 'GET':
            return obj.public or obj.user == request.user or request.user.is_superuser
        elif request.method in ('PUT', 'DELETE'):
            return obj.user == request.user or request.user.is_superuser
        else:
            return False


class IsImagePublicOrAdminOrOwnerWithAuthentication(IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return obj.public or obj.user == request.user or request.user.is_superuser


class CommentListViewPermission(IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, obj: Comment):
        return (obj.image.public and obj.user == request.user) \
               or obj.image.user == request.user or request.user.is_superuser

    def has_permission_on_image(self, request, obj: Image):
        return obj.public or obj.user == request.user or request.user.is_superuser


class CommentDetailViewPermission(IsAuthenticated):

    def has_object_permission(self, request, view, obj: Comment):
        if request.method in ('PUT', 'DELETE'):
            return (obj.image.public and obj.user == request.user) \
                   or obj.image.user == request.user or request.user.is_superuser
        else:
            return False


class ImageReportListViewPermission(AllowAny):

    def has_object_permission(self, request, view, obj: ReportImage):
        return obj.image.user is None or obj.image.user == request.user() or request.user.is_superuser

    def has_permission_on_image(self, request, obj: Image):
        if request.method == 'POST':
            return obj.public or obj.user == request.user or request.user.is_superuser
        elif request.method == 'GET':
            return obj.user is None or obj.user == request.user or request.user.is_superuser
        else:
            return False
