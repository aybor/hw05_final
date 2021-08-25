from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём пользователей:
            1) автор поста;
            2) просто ползователь.
           Создаём тестовую группу.
           В тестовой группе создаём пост.
        """
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовая группа',
        )

        # Создаём словарь с правами доступа к страницам и темплейтами
        access_response = {
            'status': HTTPStatus.OK,
            'redirect': None
        }

        not_found_response = {
            'status': HTTPStatus.NOT_FOUND,
            'redirect': None
        }

        access_for_public_pages = {
            'author': access_response,
            'authorized': access_response,
            'guest': access_response,
        }

        cls.addresses = {
            '/': {
                'access_level': access_for_public_pages,
                'template': 'posts/index.html',
            },
            '/follow/': {
                'access_level': {
                    'author': access_response,
                    'authorized': access_response,
                    'guest': {
                        'status': HTTPStatus.FOUND,
                        'redirect': '/auth/login/?next=/follow/'
                    }
                },
                'template': 'posts/index.html',
            },
            '/group/test_slug/': {
                'access_level': access_for_public_pages,
                'template': 'posts/group_list.html',
            },
            '/profile/auth/': {
                'access_level': access_for_public_pages,
                'template': 'posts/profile.html',
            },
            '/posts/1/': {
                'access_level': access_for_public_pages,
                'template': 'posts/post_view.html',
            },
            '/create/': {
                'access_level': {
                    'author': access_response,
                    'authorized': access_response,
                    'guest': {
                        'status': HTTPStatus.FOUND,
                        'redirect': '/auth/login/?next=/create/'
                    }
                },
                'template': 'posts/create_post.html',
            },
            '/posts/1/edit/': {
                'access_level': {
                    'author': access_response,
                    'authorized': {
                        'status': HTTPStatus.FOUND,
                        'redirect': '/posts/1/'
                    },
                    'guest': {
                        'status': HTTPStatus.FOUND,
                        'redirect': '/auth/login/?next=/posts/1/edit/'
                    },
                },
                'template': 'posts/create_post.html',
            },
            '/unexisting_page/': {
                'access_level': {
                    'author': not_found_response,
                    'authorized': not_found_response,
                    'guest': not_found_response,
                },
                'template': 'core/404.html',
            }
        }

    def setUp(self):
        """Создаём три клиента: не авторизованный, авторизованный
        и атворизованный автор поста.
        """
        # не авторизованный пользователь
        self.guest_client = Client()
        # авторизованный пользователь, не автор поста
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        # авторизованный пользователь, автор поста
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(PostsURLTests.user_author)
        cache.clear()

    def test_urls_exists_for_authorized_client_author(self):
        """Проверяем, что у автора поста есть доступ ко всем страницам."""

        for address, data in self.addresses.items():
            status = data['access_level']['author']['status']
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertEqual(response.status_code, status)

    def test_urls_exists_for_authorized_client(self):
        """Проверяем, что у авторизованного пользователя есть доступ
        ко всем страницам, кроме страницы редактирования поста.
        """
        for address, data in self.addresses.items():
            status = data['access_level']['authorized']['status']
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_urls_exists_for_guest_client(self):
        """ Проверяем, что у не авторизованного пользователя есть доступ
        ко всем страницам, кроме создания и редактирования поста.
        """
        for address, data in self.addresses.items():
            status = data['access_level']['guest']['status']
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_redirects_for_authorized_client(self):
        """Проверяем, что у авторизованного пользователя не автора поста
        перенаправляет на страницу поста при попытке редактирования.
        """
        for address, data in self.addresses.items():
            redirect = data['access_level']['authorized']['redirect']
            with self.subTest(address=address):
                if redirect is not None:
                    response = self.authorized_client.get(
                        address,
                        follow=True
                    )
                    self.assertRedirects(response, redirect)

    def test_redirects_for_guest_client(self):
        """Проверяем, не авторизованного пользователя перенаправляет
        на страницу входа в аккаунт при попытке создания, редактирования
        или при опытке зайти на страницу избранных пользователей.
        """
        for address, data in self.addresses.items():
            redirect = data['access_level']['guest']['redirect']
            with self.subTest(address=address):
                if redirect is not None:
                    response = self.guest_client.get(address, follow=True)
                    self.assertRedirects(response, redirect)

    def test_uses_correct_templates(self):
        """Проверяем, что urls использует корректные шаблоны.
        Для проверки используем авторизованного автора поста.
        """
        for address, data in self.addresses.items():
            template = data['template']
            with self.subTest(address=address):
                if template is not None:
                    response = self.authorized_client_author.get(address)
                    self.assertTemplateUsed(response, template)
