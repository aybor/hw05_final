from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls.base import reverse

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')

        logout_url = reverse('users:logout')
        signup_url = reverse('users:signup')
        login_url = reverse('users:login')
        password_change_url = reverse('users:password_change')
        password_change_done_url = reverse('users:password_change_done')
        password_reset_url = reverse('users:password_reset')
        password_reset_done_url = reverse('users:password_reset_done')
        password_reset_complete_url = reverse('users:password_reset_complete')

        cls.urls_for_guest = {
            password_change_url:
            f'{login_url}?next={password_change_url}',

            password_change_done_url:
            f'{login_url}?next={password_change_done_url}',
        }

        cls.urls_for_authorized = {
            signup_url: 'users/signup.html',
            login_url: 'users/login.html',
            password_change_url: 'users/password_change.html',
            password_change_done_url: 'users/password_change_done.html',
            password_reset_url: 'users/password_reset_form.html',
            password_reset_done_url: 'users/password_reset_done.html',
            password_reset_complete_url: 'users/password_reset_complete.html',
            logout_url: 'users/logged_out.html',
        }

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    def test_urls_exists_and_template_is_correct(self):
        """Проверяем доступность страниц и правильность шаблонов.
        """
        for address, template in self.urls_for_authorized.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_redirects_for_guest_client(self):
        """Проверяем, что гостевой клиент перенаправляется на страницу входа
        при попытке смены пароля.
        """

        for address, redirected in self.urls_for_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirected)
