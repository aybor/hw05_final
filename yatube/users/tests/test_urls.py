from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём пользователя."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')

    def setUp(self):
        """Создаём не авторизованный и авторизованный клиенты."""
        # не авторизованный пользователь
        self.guest_client = Client()
        # авторизованный пользователь, не автор поста
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_urls_exists_and_template_is_correct(self):
        """Проверяем доступность страниц и правильность шаблонов.
        """

        urls_for_authorized = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_change/': 'users/password_change.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/logout/': 'users/logged_out.html',
        }

        for address, template in urls_for_authorized.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_redirects_for_guest_client(self):
        """Проверяем, что гостевой клиент перенаправляется на страницу входа
        при попытке смены пароля.
        """
        urls_for_guest = {
            '/auth/password_change/':
            '/auth/login/?next=/auth/password_change/',

            '/auth/password_change/done/':
            '/auth/login/?next=/auth/password_change/done/',
        }

        for address, redirected in urls_for_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirected)
