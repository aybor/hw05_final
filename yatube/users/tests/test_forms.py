from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from users.forms import CreationForm

User = get_user_model()


class UsersCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_creation_form_create_user(self):
        user_count = User.objects.count()
        form_data = {
            'first_name': 'test_firstname',
            'last_name': 'test_lastname',
            'username': 'test_username',
            'email': 'test_email@ml.com',
            'password1': 'test_password',
            'password2': 'test_password',
        }

        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='test_firstname',
                last_name='test_lastname',
                username='test_username',
                email='test_email@ml.com'
            )
        )

    def test_creation_from_uses_correct_labels(self):
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Имя пользователя',
            'email': 'Адрес электронной почты',
        }

        for field, expected_label in labels.items():
            with self.subTest(field=field):
                label = UsersCreateFormTests.form.fields[field].label
                self.assertEqual(label, expected_label)

    def test_creation_form_uses_correct_help_texts(self):
        help_text = UsersCreateFormTests.form.fields['email'].help_text
        self.assertEqual(
            help_text,
            'Обязательное поле. Не более 150 символов.'
            'Только буквы, цифры и символы @/./+/-/_.',

        )
