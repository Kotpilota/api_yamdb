import re
from datetime import datetime

from django.core.exceptions import ValidationError


def username_validator(value):
    forbidden_values = ('me',)
    if value.lower() in forbidden_values:
        raise ValidationError(f'Недопустимое имя пользователя: {value}')

    forbidden_chars = re.sub(r'^[\w.@+-]+\Z', '', value)
    if forbidden_chars:
        raise ValidationError(
            'Недопустимые символы в имени пользователя:'
            .join(set(forbidden_chars)))

    return value


def validate_year(value):
    current_year = datetime.now().year
    if value > current_year:
        raise ValidationError(f'Year cannot be greater than {current_year}.')


def validate_score(value):
    if not (1 <= value <= 10):
        raise ValidationError(
            f'Score must be between 1 and 10. Got {value}.'
        )
