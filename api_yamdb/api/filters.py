import django_filters
from reviews.models import Title


class TitleFilter(django_filters.FilterSet):
    genre = django_filters.CharFilter(field_name='genres__slug',
                                      lookup_expr='iexact')
    category = django_filters.CharFilter(field_name='category__slug',
                                         lookup_expr='iexact')
    year = django_filters.NumberFilter(field_name='year')
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='icontains')

    class Meta:
        model = Title
        fields = ['genre', 'category', 'year', 'name']
