from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class CreationForm(UserCreationForm):
    """Форма регистрации нового пользователя."""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Имя пользователя',
            'email': 'Адрес электронной почты',
        }

        help_texts = {
            'email': 'Обязательное поле. Не более 150 символов.'
                     'Только буквы, цифры и символы @/./+/-/_.',
        }
