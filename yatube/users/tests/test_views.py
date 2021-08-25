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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.guest_client = Client()

    def test_users_pages_uses_correct_templates(self):
        """Проверем, что используются правильные шаблоны."""
        template_page_names = {
            reverse(
                'users:password_reset_complete'
            ):
            'users/password_reset_complete.html',
            reverse(
                'users:password_reset_done'
            ):
            'users/password_reset_done.html',
            reverse(
                'users:password_reset'
            ):
            'users/password_reset_form.html',
            reverse(
                'users:password_change_done'
            ):
            'users/password_change_done.html',
            reverse(
                'users:password_change'
            ):
            'users/password_change.html',
            reverse(
                'users:login'
            ):
            'users/login.html',
            reverse(
                'users:signup'
            ):
            'users/signup.html',
            reverse(
                'users:logout'
            ):
            'users/logged_out.html'
        }

        for address, template in template_page_names.items():
            with self.subTest(address=address):
                request = self.authorized_client.get(address)
                self.assertTemplateUsed(request, template)

    def test_users_sugnup_uses_correct_form(self):
        """Проверяем, что форма регистрации выводит правильные поля"""
        form_fields = {
            'first_name': forms.CharField,
            'last_name': forms.CharField,
            'username': forms.CharField,
            'email': forms.EmailField,
            'password1': forms.CharField,
            'password2': forms.CharField,
        }
        page = self.guest_client.get(reverse('users:signup'))
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = page.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
