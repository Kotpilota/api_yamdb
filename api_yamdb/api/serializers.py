from api.email_func import send_code
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import RegexValidator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.constants import EMAIL_LENGTH, USERNAME_LENGTH
from reviews.models import Category, Comment, Genre, Review, Title
from reviews.validators import username_validator

User = get_user_model()


class GenreSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Genre.
    """
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Category.
    """
    class Meta:
        model = Category
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Title для чтения.
    """

    category = CategorySerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'category', 'genres'
        )


class TitleWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Title для записи.
    """

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genres = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        slug_field='slug',
        required=True,
        allow_empty=False
    )
    rating = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'category', 'genres'
        )


class ReviewSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Review.
    """
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Review
        fields = ('id', 'author', 'text', 'score', 'pub_date')
        read_only_fields = ('author', 'title', 'pub_date')

    def validate(self, data):
        request = self.context.get('request')
        title = data.get('title') or self.instance.title
        author = request.user if request else data.get('author')

        if (self.instance is None or self.instance.title != title) and \
           Review.objects.filter(title=title, author=author).exists():
            raise serializers.ValidationError('Вы уже оставили отзыв'
                                              ' на это произведение.')

        return data


class CommentSerializer(serializers.ModelSerializer):
    """
            Сериализатор для модели Comment.
    """
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'pub_date')
        extra_kwargs = {'review': {'read_only': True}}


class GetTokenSerializer(serializers.Serializer):
    """
    Сериализатор для получения пользователем JWT-токена.
    """

    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=USERNAME_LENGTH,
        required=True
    )
    confirmation_code = serializers.CharField(
        max_length=USERNAME_LENGTH,
        required=True
    )

    def validate(self, data):
        username = data.get('username')
        user = get_object_or_404(User, username=username)
        if not default_token_generator.check_token(
            user,
            data.get('confirmation_code')
        ):
            raise serializers.ValidationError('Неверный код')
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        user.is_active = True
        user.save()
        return str(RefreshToken.for_user(user).access_token)


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для управления пользователями.
    """
    username = serializers.CharField(
        max_length=USERNAME_LENGTH,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
            )
        ],
    )
    email = serializers.EmailField(
        max_length=EMAIL_LENGTH,
        required=True,
    )
    role = serializers.ChoiceField(
        choices=['user', 'moderator', 'admin'],
        required=False,
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'bio', 'role'
        )

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" запрещено.')

        if self.instance is None and User.objects.filter(
                username=value).exists():
            raise serializers.ValidationError('Имя пользователя уже занято.')

        return value

    def validate_email(self, value):
        if self.instance is None and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Этот email уже используется.')

        return value


class NotAdminSerializer(UserSerializer):
    """
    Сериализатор для остальных пользователей."
    """

    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


class SignUpSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации.
    """
    username = serializers.CharField(
        max_length=USERNAME_LENGTH,
        validators=[username_validator],
    )
    email = serializers.EmailField(
        max_length=EMAIL_LENGTH
    )

    def validate(self, data):
        try:
            User.objects.get_or_create(
                username=data.get('username'),
                email=data.get('email')
            )
        except IntegrityError:
            raise serializers.ValidationError(
                'Такой пользователь уже существует'
            )
        return data

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']

        user, created = User.objects.get_or_create(
            username=username,
            email=email
        )
        user.save()

        send_code(user)
        return user
