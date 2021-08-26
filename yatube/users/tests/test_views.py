from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        logout_url = reverse('users:logout')
        signup_url = reverse('users:signup')
        login_url = reverse('users:login')
        password_change_url = reverse('users:password_change')
        password_change_done_url = reverse('users:password_change_done')
        password_reset_url = reverse('users:password_reset')
        password_reset_done_url = reverse('users:password_reset_done')
        password_reset_complete_url = reverse('users:password_reset_complete')

        cls.template_page_names = {
            password_reset_complete_url: 'users/password_reset_complete.html',
            password_reset_done_url: 'users/password_reset_done.html',
            password_reset_url: 'users/password_reset_form.html',
            password_change_done_url: 'users/password_change_done.html',
            password_change_url: 'users/password_change.html',
            login_url: 'users/login.html',
            signup_url: 'users/signup.html',
            logout_url: 'users/logged_out.html'
        }
        cls.form_fields = {
            'first_name': forms.CharField,
            'last_name': forms.CharField,
            'username': forms.CharField,
            'email': forms.EmailField,
            'password1': forms.CharField,
            'password2': forms.CharField,
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.guest_client = Client()

    def test_users_pages_uses_correct_templates(self):
        """Проверем, что используются правильные шаблоны."""

        for address, template in self.template_page_names.items():
            with self.subTest(address=address):
                request = self.authorized_client.get(address)
                self.assertTemplateUsed(request, template)

    def test_users_sugnup_uses_correct_form(self):
        """Проверяем, что форма регистрации выводит правильные поля"""
        page = self.guest_client.get(reverse('users:signup'))
        for field, expected in self.form_fields.items():
            with self.subTest(field=field):
                form_field = page.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
