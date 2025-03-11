# Роли пользователей:
USER = 'user'
ADMIN = 'admin'
MODERATOR = 'moderator'

ROLE_CHOICES = (
    (USER, USER),
    (ADMIN, ADMIN),
    (MODERATOR, MODERATOR),
)

# Ограничитель длинны почты:
EMAIL_LENGTH = 254

# Ограничитель на длину заголовка:
MAX_NAME_LENGTH = 256


# Ограничитель никнейма пользователей:
USERNAME_LENGTH = 150

# Ограничитель на длину slug:
MAX_SLUG_LENGTH = 50

# Ограничитель на кол-во выводимых символов в заголовке:
CHAR_OUTPUT_LIMIT = 20

# Минимальный год для успешной валидации:
MIN_YEAR = -3000

# Минимальная возможная оценка произведения:
MIN_SCORE = 1

# Максимальная возможная оценка произведения:
MAX_SCORE = 10

# Ограничитель Фамилии и Имени пользователя
MAX_FIO_LENGTH = 50