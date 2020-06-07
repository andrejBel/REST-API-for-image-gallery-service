from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.base_user import BaseUserManager
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Item, Image, Comment, Vote, Favourite, ReportImage

User = get_user_model()


class ItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name']


class CommentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'image', 'user', 'created_at', 'comment_text']
        read_only_fields = ['id', 'image', 'created_at', 'user']


class CommentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'image', 'user', 'created_at', 'comment_text']
        read_only_fields = ['id', 'created_at', 'user', 'image']


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'image', 'user', 'upvote', 'created_at']
        read_only_fields = ['id', 'image', 'user', 'created_at']


class VoteCreateSerializer(serializers.Serializer):
    type = serializers.CharField(required=True)

    class Meta:
        fields = ["type"]

    def validate_type(self, value):
        if value not in ('up', 'down', 'undo'):
            raise serializers.ValidationError("Type not in ('up', 'down', 'undo')")
        return value


class FavouritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourite
        fields = ['id', 'image', 'user']
        read_only_fields = ['id', 'image', 'user']


class FavouriteCreateSerializer(serializers.Serializer):
    type = serializers.CharField(required=True)

    class Meta:
        fields = ["type"]

    def validate_type(self, value):
        if value not in ('add', 'remove'):
            raise serializers.ValidationError("Type not in ('add', 'remove')")
        return value


class ReportImageListSerilizer(serializers.ModelSerializer):
    class Meta:
        model = ReportImage
        fields = ['id', 'image', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'image', 'user', 'created_at']


class ImageListSerializer(serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    downvote_count = serializers.SerializerMethodField()
    favourite_count = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'user', 'created_at', 'title', 'description', 'file', "public", "comment_count",
                  "upvote_count", 'downvote_count', "favourite_count", "report_count"]
        read_only_fields = ["id", 'user', 'created_at']
        extra_kwargs = {
            'file': {'read_only': False},
        }

    def validate_public(self, value):
        if value is None:
            raise serializers.ValidationError("public is required")
        user = self.context['request'].user
        if not user.is_authenticated and not value:
            raise serializers.ValidationError("Anonymous user can have only public images")
        return value

    def get_comment_count(self, image: Image):
        return image.comment_to_image.count()

    def get_upvote_count(self, image: Image):
        return image.vote_to_image.filter(upvote=True).count()

    def get_downvote_count(self, image: Image):
        return image.vote_to_image.filter(upvote=False).count()

    def get_favourite_count(self, image: Image):
        return image.favourite_to_image.count()

    def get_report_count(self, image: Image):
        return image.report_to_image.count()


class ImageDetailSerializer(serializers.ModelSerializer):
    comments = CommentListSerializer(many=True, required=False, source="comment_to_image", read_only=True)
    votes = VoteSerializer(many=True, required=False, source="vote_to_image", read_only=True)
    favourites = FavouritesSerializer(many=True, required=False, source='favourite_to_image', read_only=True)
    reports = ReportImageListSerilizer(many=True, required=False, source='report_to_image', read_only=True)
    public = serializers.NullBooleanField(required=False)

    class Meta:
        model = Image
        fields = ['id', 'user', 'created_at', 'title', 'description', 'public', 'file', "comments",
                  "votes", "favourites", "reports"]
        read_only_fields = ['id', 'user', 'created_at', 'file', 'comments', 'votes', 'favourites', "reports"]
        # extra_kwargs = {
        #     'uploaded_by': {'write_only': True},
        # }


class UserSerializer(serializers.ModelSerializer):
    images = ImageDetailSerializer(many=True, required=False)
    comments = CommentListSerializer(many=True, required=False, source="comment_to_user")
    votes = VoteSerializer(many=True, required=False, source="vote_to_user")
    favourites = FavouritesSerializer(many=True, required=False, source="favourite_to_user")

    class Meta:
        model = User
        fields = ['id', 'username', 'images', "comments", 'votes', "favourites"]


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('password', 'username', 'email')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_username(self, value):
        user = User.objects.filter(username=value)
        if user:
            raise serializers.ValidationError("Username is already taken")
        return value

    def validate_email(self, value):
        user = User.objects.filter(email=value)
        if user:
            raise serializers.ValidationError("Email is already taken")
        return BaseUserManager.normalize_email(value)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class UserUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=False)
    email = serializers.CharField(required=False)

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Current password does not match')
        return value

    def validate_new_password(self, value):
        if value is not None:
            password_validation.validate_password(value)
        return value

    def validate_email(self, value):
        if value is not None:
            user = User.objects.filter(email=value)
            if user:
                raise serializers.ValidationError("Email is already taken")
            return BaseUserManager.normalize_email(value)
        return value

    class Meta:
        fields = ('current_password', 'new_password', 'email')


class AuthenticationUserSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(help_text="Token for authentication")

    class Meta:
        model = User
        fields = ('id', 'password', 'username', 'email', 'token')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def get_token(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return token.key


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=1, help_text="user's username")
    password = serializers.CharField(write_only=True, min_length=1, style={'input_type': 'password'},
                                     help_text="user's password")

    class Meta:
        fields = ("username", "password")


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """
    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )
