from django.conf import settings
from django.utils.translation import gettext_lazy as gt


from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (
    ADMIN, CHAR_OUTPUT_LIMIT, EMAIL_LENGTH, MAX_NAME_LENGTH,
    MAX_SLUG_LENGTH, MODERATOR, ROLE_CHOICES, USER,
    USERNAME_LENGTH, MAX_FIO_LENGTH
)
from .validators import username_validator


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
        max_length=10, choices=ROLE_CHOICES, default=USER, verbose_name='Role'
    )

    class Meta:
        ordering = ('username', 'id',)
        verbose_name = 'User'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]

    @property
    def is_admin(self):
        """Checks if the user has administrator rights."""
        return self.role == ADMIN or self.is_superuser or self.is_staff

    @property
    def is_moderator(self):
        """Checks whether the user has moderator rights."""
        return self.role == MODERATOR or self.is_admin

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name=gt('Name')
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH, unique=True, verbose_name=gt('Slug')
    )

    class Meta:
        verbose_name = gt('Category')
        verbose_name_plural = gt('Categories')
        ordering = ['name']

    def __str__(self):
        return self.name[:CHAR_OUTPUT_LIMIT]


class Genre(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name=gt('Name')
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH, unique=True, verbose_name=gt('Slug')
    )

    class Meta:
        verbose_name = gt('Genre')
        verbose_name_plural = gt('Genres')
        ordering = ['name']

    def __str__(self):
        return self.name[:CHAR_OUTPUT_LIMIT]


class Title(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH, verbose_name=gt('Name')
    )
    year = models.PositiveIntegerField(verbose_name=gt('Year'))
    rating = models.IntegerField(
        null=True, blank=True, verbose_name=gt('Rating')
    )
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
    
    def compute_rating(self):
        # Пересчет средней оценки на основе связанных отзывов
        reviews = self.reviews.all()
        self.rating = reviews.aggregate(models.Avg('score'))['score__avg']
        self.save()
    
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
        verbose_name=gt('Score'), help_text=gt('Rating from 1 to 10')
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name=gt('Publication date'))

    class Meta:
        verbose_name = gt('Review')
        verbose_name_plural = gt('Reviews')
        ordering = ['-pub_date']
        unique_together = ('title', 'author')

    def __str__(self):
        return f'Review by {self.author} on {self.title}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.title.compute_rating()

    def delete(self, *args, **kwargs):
        title = self.title
        super().delete(*args, **kwargs)
        title.compute_rating()



class Comment(models.Model):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comments', verbose_name=gt('Review')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', verbose_name=gt('Author')
    )
    text = models.TextField(verbose_name=gt('Comment text'))
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name=gt('Publication date'))

    class Meta:
        verbose_name = gt('Comment')
        verbose_name_plural = gt('Comments')
        ordering = ['-pub_date']

    def __str__(self):
        return f'Comment by {self.author} on {self.review}'
