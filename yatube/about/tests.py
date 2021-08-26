from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutURLViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём пользователя."""
        super().setUpClass()

        user_username = 'user'
        cls.user = User.objects.create_user(username=user_username)

        about_author_url = reverse('about:author')
        about_author_template = 'about/author.html'

        about_tech_url = reverse('about:tech')
        about_tech_template = 'about/tech.html'

        cls.addresses = {
            about_author_url: {
                'status': HTTPStatus.OK,
                'template': about_author_template
            },
            about_tech_url: {
                'status': HTTPStatus.OK,
                'template': about_tech_template
            },
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_exists_and_templates(self):
        """Проверяем доступность и темплейты страниц about"""
        for address, data in self.addresses.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                status = data['status']
                template = data['template']
                self.assertEqual(response.status_code, status)
                self.assertTemplateUsed(response, template)
