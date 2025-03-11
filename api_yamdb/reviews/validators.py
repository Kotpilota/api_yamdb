import re

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