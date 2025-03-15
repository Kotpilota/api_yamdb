from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as gt

from .constants import (CHAR_OUTPUT_LIMIT, EMAIL_LENGTH, MAX_FIO_LENGTH,
                        MAX_NAME_LENGTH, MAX_SLUG_LENGTH,
                        USERNAME_LENGTH, RoleChoices)
from .validators import username_validator, validate_year, validate_score


class User(AbstractUser):
    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True, validators=[username_validator], verbose_name='Username'
    )
    email = models.EmailField(
        max_length=EMAIL_LENGTH, unique=True, verbose_name='Email'
    )
    first_name = models.CharField(
        max_length=MAX_FIO_LENGTH, blank=True, verbose_name='First Name'
    )
    last_name = models.CharField(
        max_length=MAX_FIO_LENGTH, blank=True, verbose_name='Last Name'
    )
    bio = models.TextField(
        blank=True, verbose_name='BIO'
    )
    role = models.CharField(
        max_length=max(len(role) for role in RoleChoices.values),
        choices=RoleChoices.choices,
        default=RoleChoices.USER,
        verbose_name='Role'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'User'

    @property
    def is_admin(self):
        """Checks if the user has administrator rights."""
        return self.role == RoleChoices.ADMIN or self.is_superuser or self.is_staff

    @property
    def is_moderator(self):
        """Checks whether the user has moderator rights."""
        return self.role == RoleChoices.MODERATOR or self.is_admin

    def __str__(self):
        return self.username


class BaseNameSlugModel(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name=gt('Name')
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH, unique=True, verbose_name=gt('Slug')
    )

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name[:CHAR_OUTPUT_LIMIT]


class Category(BaseNameSlugModel):
    class Meta(BaseNameSlugModel.Meta):
        verbose_name = gt('Category')
        verbose_name_plural = gt('Categories')


class Genre(BaseNameSlugModel):
    class Meta(BaseNameSlugModel.Meta):
        verbose_name = gt('Genre')
        verbose_name_plural = gt('Genres')


class Title(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name=gt('Name')
    )
    year = models.IntegerField(verbose_name='Year', validators=[validate_year])
    description = models.TextField(
        null=True, blank=True, verbose_name=gt('Description')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name=gt('Category')
    )
    genres = models.ManyToManyField(
        Genre, related_name='titles', verbose_name=gt('Genres')
    )

    class Meta:
        verbose_name = gt('Title')
        verbose_name_plural = gt('Titles')
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        current_year = datetime.now().year
        if self.year > current_year:
            raise ValidationError({"year": "Year cannot be greater than"
                                   f" {current_year}."})


class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=gt('Title')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=gt('Author')
    )
    text = models.TextField(verbose_name=gt('Review text'))
    score = models.PositiveSmallIntegerField(
        verbose_name=gt('Score'),
        help_text=gt('Rating from 1 to 10'),
        validators=[MinValueValidator(1), MaxValueValidator(10),
                    validate_score]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name=gt('Publication date')
    )

    class Meta:
        verbose_name = gt('Review')
        verbose_name_plural = gt('Reviews')
        ordering = ['-pub_date']
        unique_together = ('title', 'author')

    def __str__(self):
        return f'Review by {self.author} on {self.title}'


class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gt('Review')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=gt('Author')
    )
    text = models.TextField(verbose_name=gt('Comment text'))
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=gt('Publication date')
    )

    class Meta:
        verbose_name = gt('Comment')
        verbose_name_plural = gt('Comments')
        ordering = ['-pub_date']

    def __str__(self):
        return f"Comment by {self.author} on {self.review}"
