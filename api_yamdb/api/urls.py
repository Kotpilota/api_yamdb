from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, ReviewViewSet, get_token, signup, \
    TitleViewSet, GenreViewSet, CategoryViewSet, UserViewSet

router = DefaultRouter()

router.register('titles', TitleViewSet, basename='titles')
router.register('categories', CategoryViewSet, basename='categories')
router.register('genres', GenreViewSet, basename='genres')
router.register('users', UserViewSet, basename='users')

router.register(r'titles/(?P<title_id>\d+)/reviews', ReviewViewSet, basename='review')
router.register(r'titles/(?P<title_id>\d+)/reviews/(?P<review_pk>\d+)/comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('auth/signup/', signup, name='signup'),
    path('auth/token/', get_token, name='token'),
    path('', include(router.urls)),
]