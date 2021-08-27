from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls.base import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        author_username = 'auth'
        user_username = 'user'
        test_group_title = 'Тестовая группа'
        test_slug = 'test_slug'
        test_group_description = 'Тестовое описание'
        test_post_text = 'Тестовый текст'

        cls.user_author = User.objects.create_user(
            username=author_username
        )
        cls.user = User.objects.create_user(
            username=user_username
        )
        cls.group = Group.objects.create(
            title=test_group_title,
            slug=test_slug,
            description=test_group_description,
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text=test_post_text,
        )

        login_url = reverse('users:login')

        index_url = '/'
        follow_url = '/follow/'
        group_url = f'/group/{cls.group.slug}/'
        profile_url = f'/profile/{cls.user_author.username}/'
        post_url = f'/posts/{cls.post.pk}/'
        create_url = '/create/'
        post_edit_url = f'/posts/{cls.post.pk}/edit/'
        unexisting_url = '/unexisting_page/'

        follow_redirect_url = f'{login_url}?next={follow_url}'
        create_redirect_url = f'{login_url}?next={create_url}'
        post_edit_success_redirect = f'/posts/{cls.post.pk}/'
        post_edit_guest_redirect = f'{login_url}?next={post_edit_url}'

        index_template = 'posts/index.html'
        follow_template = index_template
        group_template = 'posts/group_list.html'
        profile_template = 'posts/profile.html'
        post_template = 'posts/post_view.html'
        create_template = 'posts/create_post.html'
        post_edit_template = create_template
        unexisting_template = 'core/404.html'

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
            index_url: {
                'access_level': access_for_public_pages,
                'template': index_template,
            },
            follow_url: {
                'access_level': {
                    'author': access_response,
                    'authorized': access_response,
                    'guest': {
                        'status': HTTPStatus.FOUND,
                        'redirect': follow_redirect_url
                    }
                },
                'template': follow_template,
            },
            group_url: {
                'access_level': access_for_public_pages,
                'template': group_template,
            },
            profile_url: {
                'access_level': access_for_public_pages,
                'template': profile_template,
            },
            post_url: {
                'access_level': access_for_public_pages,
                'template': post_template,
            },
            create_url: {
                'access_level': {
                    'author': access_response,
                    'authorized': access_response,
                    'guest': {
                        'status': HTTPStatus.FOUND,
                        'redirect': create_redirect_url
                    }
                },
                'template': create_template,
            },
            post_edit_url: {
                'access_level': {
                    'author': access_response,
                    'authorized': {
                        'status': HTTPStatus.FOUND,
                        'redirect': post_edit_success_redirect
                    },
                    'guest': {
                        'status': HTTPStatus.FOUND,
                        'redirect': post_edit_guest_redirect
                    },
                },
                'template': post_edit_template,
            },
            unexisting_url: {
                'access_level': {
                    'author': not_found_response,
                    'authorized': not_found_response,
                    'guest': not_found_response,
                },
                'template': unexisting_template,
            }
        }

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)

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
