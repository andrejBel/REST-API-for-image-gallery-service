from django.urls import path
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.views import obtain_auth_token

from .views.comment import views as comment_views
from .views.image import views as image_views
from .views.user import views as user_views

app_name = 'restapi'
obtain_auth_token = swagger_auto_schema(obtain_auth_token, auto_schema=None)
urlpatterns = [

    path('images/', image_views.ImageListView.as_view(), name='images'),
    path('images/trending', image_views.ImageTrendingListView.as_view()),
    path('images/<int:pk>', image_views.ImageDetailView.as_view()),
    path('images/<int:pk>/comment', comment_views.CommentListView.as_view()),
    path('images/<int:pk>/vote', image_views.ImageVoteView.as_view()),
    path('images/<int:pk>/report', image_views.ImageReportListView.as_view()),
    path('images/<int:pk>/favourite', image_views.ImageFavouriteView.as_view()),

    path('me/images', image_views.ImageUserView.as_view()),
    path('me/images/voted', image_views.ImageVoteListView.as_view()),
    path('me/images/favourites', image_views.ImageFavouriteListView.as_view()),
    path('me/images/favourites/download', image_views.UserFavouriteImagesView.as_view()),
    path('me/profile', user_views.ChangeUserDetailView.as_view()),

    path('comment/<int:pk>', comment_views.CommentDetailView.as_view()),

    path('users/', user_views.UserList.as_view()),
    path('users/<int:pk>/', user_views.UserDetail.as_view()),

    path('register/', user_views.RegisterUserView.as_view()),
    path('login/', user_views.LoginView.as_view()),
    path('logout/', user_views.LogoutView.as_view()),

    path('login/<str:backend>/', user_views.social_login_view),

]
