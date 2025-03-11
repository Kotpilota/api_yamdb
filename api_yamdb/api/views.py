from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, \
    IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from api.permissions import IsAdminOrReadOnly, IsAuthorOrModerPermission, IsAdminOrStaffPermission

from reviews.constants import USER
from reviews.models import Comment, Review, Category, Title, Genre
from .email_func import send_code
from .serializers import CommentSerializer, ReviewSerializer, \
    TokenSerializer, SignUpSerializer, TitleSerializer, GenreSerializer, \
    CategorySerializer, UserSerializer, NotAdminSerializer

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

    def get_queryset(self):
        queryset = super().get_queryset()
        username = self.request.query_params.get('search')
        if username:
            queryset = queryset.filter(username__icontains=username)
        return queryset

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

        if request.method == 'PATCH':
            serializer = NotAdminSerializer(
                request.user, data=request.data, partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Удаление пользователя. Только для администраторов и суперпользователей.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TitleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления произведениями (Title).
    """
    serializer_class = TitleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    queryset = Title.objects.all()

    http_method_names = ['get', 'patch', 'post', 'delete']

    def get_queryset(self):
        qs = Title.objects.all()
        genre_slug = self.request.query_params.get('genre')
        if genre_slug:
            qs = qs.filter(genres__slug=genre_slug)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(year=year)
        name = self.request.query_params.get('name')
        if name:
            qs = qs.filter(name__icontains=name)
        return qs

    def perform_create(self, serializer):
        serializer.save()


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    ViewSet для категорий.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        search_query = self.request.query_params.get('search')
        if search_query:
            qs = qs.filter(name__icontains=search_query)
        return qs


class GenreViewSet(mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    ViewSet для жанров.
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        search_query = self.request.query_params.get('search')
        if search_query:
            qs = qs.filter(name__icontains=search_query)
        return qs


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """Регистрация пользователя и отправка кода подтверждения."""
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email']

    try:
        user, created = User.objects.get_or_create(
            username=username,
            email=email,
            defaults={'role': USER}
        )

        send_code(user)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except IntegrityError:
        return Response(
            {'error': 'Пользователь с таким именем или email уже существует'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def get_token(request):
    """Получение JWT-токена по коду подтверждения."""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    confirmation_code = serializer.validated_data['confirmation_code']

    user = get_object_or_404(User, username=username)

    if not default_token_generator.check_token(user, confirmation_code):
        return Response(
            {'error': 'Неверный код подтверждения'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.is_active:
        user.is_active = True
        user.save()

    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)

    return Response({'token': token}, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrModerPermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrModerPermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)