from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from reviews.models import Category, Genre, Review, Title

from api.permissions import (IsAdminOrReadOnly, IsAdminOrStaffPermission,
                             IsAuthorOrModerPermission)
from .serializers import (CategorySerializer, CommentSerializer,
                          GenreSerializer, GetTokenSerializer,
                          NotAdminSerializer, ReviewSerializer,
                          SignUpSerializer, TitleReadSerializer,
                          TitleWriteSerializer,
                          UserSerializer)

from .filters import TitleFilter

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrStaffPermission]
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (SearchFilter,)
    search_fields = ('username',)

    @action(
        detail=False, methods=['get', 'patch'],
        permission_classes=[IsAuthenticated], url_path='me'
    )
    def me(self, request):
        """
        Эндпоинт /api/v1/users/me/ для работы с текущим пользователем.
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        request.data._mutable = True
        if 'role' in request.data:
            request.data.pop('role')
            request.data._mutable = False

        serializer = NotAdminSerializer(
            request.user, data=request.data, partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class TitleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления произведениями (Title).
    """
    permission_classes = [IsAdminOrReadOnly,]
    queryset = Title.objects.all()
    filterset_class = TitleFilter

    http_method_names = ['get', 'patch', 'post', 'delete']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleReadSerializer
        return TitleWriteSerializer

    def get_queryset(self):
        return Title.objects.annotate(
            rating=Avg('reviews__score')
        )


class BaseCategoryGenreViewSet(mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    """
    Базовый ViewSet для категорий и жанров.
    """

    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'


class CategoryViewSet(BaseCategoryGenreViewSet):
    """
    ViewSet для управления категориями.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class GenreViewSet(BaseCategoryGenreViewSet):
    """
    ViewSet для управления жанрами.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    Viewset для управления отзывами.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthorOrModerPermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_title(self):
        """
        Получить объект Title, удостоверясь, что он существует.
        """
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Title, pk=title_id)

    def get_queryset(self):
        title = self.get_title()
        return title.reviews.all()

    def perform_create(self, serializer):
        title = self.get_title()

        existing_review = Review.objects.filter(
            title=title, author=self.request.user
        )
        if existing_review.exists():
            raise ValidationError('Вы уже оставили отзыв на это произведение.')

        serializer.save(author=self.request.user, title=title)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Регистрация пользователя и отправка кода подтверждения."""
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """Получение JWT-токена по коду подтверждения."""
    serializer = GetTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.save()
    return Response({'token': token}, status=status.HTTP_200_OK)


class CommentViewSet(viewsets.ModelViewSet):
    """
    Viewset для комментариев.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrModerPermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_review(self):
        """
        Получаем объект Review, при связи с Title.
        """
        review_id = self.kwargs.get('review_pk')
        title_id = self.kwargs.get('title_id')
        return get_object_or_404(Review, pk=review_id, title_id=title_id)

    def get_queryset(self):
        review = self.get_review()
        return review.comments.all()

    def perform_create(self, serializer):
        review = self.get_review()
        serializer.save(author=self.request.user, review=review)
