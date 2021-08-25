from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AboutURLViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём пользователя."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')

        cls.addresses = {
            reverse('about:author'): {
                'status': HTTPStatus.OK,
                'template': 'about/author.html'
            },
            reverse('about:tech'): {
                'status': HTTPStatus.OK,
                'template': 'about/tech.html'
            },
        }

    def setUp(self):
        """Создаём не авторизованный клиент."""
        # не авторизованный пользователь
        self.guest_client = Client()

    def test_about_pages_exists_and_templates(self):
        """Проверяем доступность и тесплейты страниц about/"""
        for address, data in self.addresses.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                status = data['status']
                template = data['template']
                self.assertEqual(response.status_code, status)
                self.assertTemplateUsed(response, template)
