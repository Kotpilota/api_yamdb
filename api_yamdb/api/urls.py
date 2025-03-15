from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CommentViewSet,
    GenreViewSet,
    ReviewViewSet,
    TitleViewSet,
    UserViewSet,
    get_token,
    signup,
)

v_1router = DefaultRouter()

v_1router.register('titles', TitleViewSet, basename='titles')
v_1router.register('categories', CategoryViewSet, basename='categories')
v_1router.register('genres', GenreViewSet, basename='genres')
v_1router.register('users', UserViewSet, basename='users')

v_1router.register(
    r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, basename='review'
)
v_1router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_pk>\d+)/comments',
    CommentViewSet,
    basename='comment'
)

urlpatterns = [
    path('v1/auth/signup/', signup, name='signup'),
    path('v1/auth/token/', get_token, name='token'),
    path('v1/', include(v_1router.urls)),
]
