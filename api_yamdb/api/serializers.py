from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.core.validators import RegexValidator
from reviews.constants import USERNAME_LENGTH, EMAIL_LENGTH
from reviews.models import Comment, Review, Genre, Category, Title
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


class TitleSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=256)
    year = serializers.IntegerField()
    description = serializers.CharField(allow_blank=True, required=False)
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        slug_field='slug',
        source="genres"
    )
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'category', 'genre'
        )

    def to_representation(self, instance):
        """
        Формируем вложенное представление для category и жанров.
        """
        rep = super().to_representation(instance)
        rep['category'] = CategorySerializer(
            instance.category
        ).data if instance.category else None
        rep['genre'] = GenreSerializer(instance.genres.all(), many=True).data
        return rep

    def validate_year(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("Год должен быть числом.")
        return value

    def create(self, validated_data):
        genres = validated_data.pop('genres', [])
        instance = Title.objects.create(**validated_data)
        instance.genres.set(genres)
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    class Meta:
        model = Review
        fields = ('id', 'title', 'author', 'text', 'score', 'pub_date')
        read_only_fields = ('author', 'title', 'pub_date')

    def validate_score(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError("Score must be between 1 and 10.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'review', 'author', 'text', 'pub_date')
        extra_kwargs = {'review': {'read_only': True}}

class TokenSerializer(serializers.Serializer):
    """Сериализатор для получения JWT-токена."""
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=USERNAME_LENGTH,
        required=True
    )
    confirmation_code = serializers.CharField(
        max_length=USERNAME_LENGTH,
        required=True
    )


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для управления пользователями.
    """
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Имя пользователя содержит недопустимые символы. Разрешены только буквы, цифры и @/./+/-/_'
            )
        ],
        help_text="Имя пользователя должно содержать только разрешённые символы."
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        help_text="Введите корректный email-адрес."
    )
    role = serializers.ChoiceField(
        choices=['user', 'moderator', 'admin'],
        required=False,
        help_text="Роль пользователя. Может быть 'user', 'moderator' или 'admin'."
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
    """Сериализатор для остальных пользователей."""

    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)



class SignUpSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации.
    """
    username = serializers.CharField(
        max_length=150,
        validators=[username_validator],
        required=True,
        help_text="Имя пользователя должно содержать только допустимые символы."
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        help_text="Введите корректный email-адрес."
    )

    def validate_username(self, value):
        """
        Проверка на недопустимые имена и длину.
        """
        if len(value) > 150:
            raise serializers.ValidationError(
                'Имя пользователя не может превышать 150 символов.')
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" запрещено.')
        return value

    def validate_email(self, value):
        """
        Проверка уникальности и корректности email.
        """
        if len(value) > 254:
            raise serializers.ValidationError(
                'Email не может превышать 254 символа.')
        return value
