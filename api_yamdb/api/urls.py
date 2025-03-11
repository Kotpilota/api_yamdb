from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, ReviewViewSet, get_token, signup, \
    TitleViewSet, GenreViewSet, CategoryViewSet, UserViewSet

router = DefaultRouter()
router.register('reviews', ReviewViewSet, basename='review')

router.register(
    r'reviews/(?P<review_pk>\d+)/comments', CommentViewSet,
    basename='review-comments'
)
router.register('titles', TitleViewSet, basename='titles')
router.register('categories', CategoryViewSet, basename='categories')
router.register('genres', GenreViewSet, basename='genres')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/signup/', signup, name='signup'),
    path('auth/token/', get_token, name='token'),
    path('', include(router.urls)),
]