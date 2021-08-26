import shutil
import tempfile

from faker import Faker
from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from posts.models import Post, Group, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def random_time():
    fake = Faker()
    return fake.date_time_between(start_date='-100y', end_date='now')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        # Создаём 14 постов без группы, со случайным временем
        posts = [
            Post(
                author=cls.user,
                text='Тестовый текст',
                pub_date=random_time(),
            )
            for i in range(14)
        ]

        # Добавляем 14 постов с группой, со случайным временем, с картинкой
        posts.extend(
            [
                Post(
                    author=cls.user,
                    text='Тестовый текст для поста с группой',
                    image=cls.uploaded,
                    group=cls.group,
                    pub_date=random_time(),
                ) for i in range(14)
            ]
        )

        # Добавляем 1 пост без группы, c другим пользователем,
        # с автодобавлением времени
        posts.append(
            Post(
                author=cls.user2,
                text='Тестовый текст',
            )
        )

        # Записываем посты в базу
        Post.objects.bulk_create(posts)

        cls.index_url = reverse('posts:index')
        cls.group_url = reverse(
            'posts:group_posts',
            kwargs={'slug': 'test_slug'}
        )
        cls.auth_url = reverse('posts:profile', kwargs={'username': 'auth'})
        cls.user2_url = reverse('posts:profile', kwargs={'username': 'user'})
        cls.follow_index_url = reverse('posts:follow_index')
        cls.follow_url = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user2.username}
        )
        cls.unfollow_url = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user2.username}
        )

        cls.template_page_names = {
            cls.index_url: 'posts/index.html',
            cls.follow_index_url: 'posts/index.html',
            cls.group_url: 'posts/group_list.html',
            cls.auth_url: 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): 'posts/post_view.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаём авторизованного и неавторизованного клиента."""

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()
        cache.clear()

    def test_pages_uses_correct_templates(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""

        for reverse_name, template in self.template_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context_with_paginator(self):
        """Проверяем, что:
        1) пагинатор сработал и выводит правильное
        количество постов на страницу;
        2) на страницах правильный контекст;
        3) посты на страницах отсортированы по возрастанию даты добавления.
        Всего три страницы: 10, 10 и 9 постов.
        """
        # запоминаем содержание страниц
        first_page = self.authorized_client.get(self.index_url)
        second_page = self.authorized_client.get(
            self.index_url + '?page=2'
        )
        third_page = self.authorized_client.get(
            self.index_url + '?page=3'
        )

        pages = {
            first_page: 10,
            second_page: 10,
            third_page: 9,
        }
        for page, length in pages.items():
            with self.subTest(page=page):
                # проверяем правильность работы пагинатора
                self.assertEqual(len(page.context['page_obj']), length)
                for number in range(length):
                    with self.subTest(number=number):
                        post = page.context['page_obj'][number]

                        # проверяем правильность автора
                        # в каждом посте на странице
                        self.assertIn(
                            post.author.username,
                            ('auth', 'user')
                        )

                        # проверяем правильность указания группы
                        # при её наличии, текста поста для группы и картинки
                        if post.group:
                            self.assertEqual(
                                post.group.title,
                                'Тестовая группа'
                            )
                            self.assertEqual(
                                post.text,
                                'Тестовый текст для поста с группой'
                            )
                            self.assertEqual(
                                post.image,
                                Post.objects.get(pk=post.pk).image
                            )
                        else:

                            # проверяем текст поста без группы
                            self.assertEqual(post.text, 'Тестовый текст')

                for number in range(length - 1):
                    # проверяем, что посты на странице отсортированы по дате
                    with self.subTest(number=number):
                        self.assertGreaterEqual(
                            page.context['page_obj'][number].pub_date,
                            page.context['page_obj'][number + 1].pub_date
                        )

    def test_group_list_correct_context_with_paginator(self):
        """Проверяем, что:
        1) пагинатор сработал и выводит правильное
        количество постов на страницу;
        2) на страницах правильный контекст;
        3) посты на страницах отсортированы по возрастанию даты добавления.
        Всего три страницы: 10, 10 и 9 постов.
        4) выведены только посты с указанной группой
        """

        first_page = self.authorized_client.get(self.group_url)
        second_page = self.authorized_client.get(
            self.group_url + '?page=2'
        )

        pages = {
            first_page: 10,
            second_page: 4
        }

        for page, length in pages.items():
            with self.subTest(page=page):
                # проверяем правильность работы пагинатора
                self.assertEqual(len(page.context['page_obj']), length)
                for number in range(length):
                    with self.subTest(number=number):
                        post = page.context['page_obj'][number]
                        # проверяем правильность автора
                        # в каждом посте на странице
                        self.assertEqual(post.author.username, 'auth')

                        # проверяем, что выведены только посты группы,
                        # правильность текста, правильность картинки
                        self.assertEqual(post.group.title, 'Тестовая группа')
                        self.assertEqual(
                            post.text,
                            'Тестовый текст для поста с группой'
                        )
                        self.assertEqual(
                            post.image,
                            Post.objects.get(pk=post.pk).image
                        )

                for number in range(length - 1):
                    # проверяемб что посты на странице отсортированы по дате
                    with self.subTest(number=number):
                        self.assertGreaterEqual(
                            page.context['page_obj'][number].pub_date,
                            page.context['page_obj'][number + 1].pub_date
                        )

    def test_profile_correct_context_with_paginator(self):
        """Проверяем, что:
        1) пагинатор сработал и выводит правильное
        количество постов на страницу;
        2) на страницах правильный контекст;
        3) посты на страницах отсортированы по возрастанию даты добавления.
        Всего три страницы: 10, 10 и 9 постов;
        4) выведены только посты автора auth
        """
        # запоминаем содержание страниц
        first_page = self.authorized_client.get(self.auth_url)

        second_page = self.authorized_client.get(
            self.auth_url + '?page=2'
        )

        third_page = self.authorized_client.get(
            self.auth_url + '?page=3'
        )

        pages = {
            first_page: 10,
            second_page: 10,
            third_page: 8,
        }

        for page, length in pages.items():
            with self.subTest(page=page):
                # проверяем правильность работы пагинатора
                self.assertEqual(len(page.context['page_obj']), length)
                for number in range(length):
                    with self.subTest(number=number):
                        post = page.context['page_obj'][number]
                        # проверяем правильность автора
                        # в каждом посте на странице
                        self.assertEqual(post.author.username, 'auth')

                        # проверяем правильность указания группы
                        # при её наличии, текста поста для группы, картинки
                        if post.group:
                            self.assertEqual(
                                post.group.title,
                                'Тестовая группа'
                            )
                            self.assertEqual(
                                post.text,
                                'Тестовый текст для поста с группой'
                            )
                            self.assertEqual(
                                post.image,
                                Post.objects.get(pk=post.pk).image
                            )

                        else:
                            # проверяем текст поста без группы
                            self.assertEqual(post.text, 'Тестовый текст')

                for number in range(length - 1):
                    # проверяемб что посты на странице отсортированы по дате
                    with self.subTest(number=number):
                        self.assertGreaterEqual(
                            page.context['page_obj'][number].pub_date,
                            page.context['page_obj'][number + 1].pub_date
                        )

    def test_post_detail_correct_context(self):
        """Проверяем, что для каждой записи в базе выводится пост
        с правильным контекстом.
        """

        for post in Post.objects.all():
            page = self.authorized_client.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': post.id}
                )
            )
            with self.subTest(post=post):
                self.assertIn(
                    page.context['post'].text,
                    (
                        'Тестовый текст для поста с группой',
                        'Тестовый текст',
                    )
                )
                if post.group:
                    self.assertEqual(
                        page.context['post'].group,
                        post.group
                    )
                    self.assertEqual(
                        post.image,
                        Post.objects.get(pk=post.pk).image
                    )

                self.assertIn(
                    page.context['post'].author.username,
                    ('auth', 'user')
                )

                self.assertEqual(page.context['post'].pub_date, post.pub_date)
                self.assertEqual(
                    page.context['author_posts_cnt'],
                    post.author.posts.count()
                )

    def test_post_edit_correct_form_and_context(self):
        """Проверяем, что для каждой записи пользователя auth
        выводится форма редактирования с правильным контекстом.
        """
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for post in self.user.posts.all():
            page = self.authorized_client.get(
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': post.id}
                )
            )
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = page.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

            with self.subTest(post=post):
                self.assertTrue(page.context['is_edit'])
                self.assertIn(
                    page.context['post'].text,
                    (
                        'Тестовый текст для поста с группой',
                        'Тестовый текст',
                    )
                )
                if post.group:
                    self.assertEqual(
                        page.context['post'].group,
                        post.group
                    )

                self.assertIn(
                    page.context['post'].author.username,
                    ('auth', 'user')
                )

                self.assertEqual(page.context['post'].pub_date, post.pub_date)

    def test_create_post_correct_form_and_creation(self):
        """Проверяем, что на страницу создания поста выводятся
        корректные поля.
        """

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        page = self.authorized_client.get(reverse('posts:post_create'))

        # проверяем правильность полей
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = page.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        # создаём ещё одноу группу
        yet_another_group = Group.objects.create(
            title='YanGroup',
            slug='yangroup',
            description='Прогресс неостановим'
        )

        # создаём ещё один пост от в новой группе
        yet_another_post = Post.objects.create(
            author=self.user,
            text='Текст для дополнительной проверки',
            group=yet_another_group,
            pub_date=random_time(),
        )

        # проверяем, что пост отображается по своему id
        post_page = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': yet_another_post.id}
            )
        )
        self.assertEqual(post_page.context['post'], yet_another_post)

        main_page = self.authorized_client.get(
            reverse(
                'posts:index'
            )
        )

        group_page = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': yet_another_group.slug}
            )
        )

        user_page = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )

        # проверяем, что пост отображается первым на
        # главной странице, странице пользователя и странице группы
        for page in main_page, group_page, user_page:
            with self.subTest(page=page):
                self.assertEqual(page.context['page_obj'][0], yet_another_post)

        # проверяем, что пост не попал в другую группу
        self.assertNotIn(yet_another_post, self.group.posts.all())

    def test_index_cache(self):
        """Тестирование кеширования главной страницы."""
        # Считаем сколько постов в базе
        posts_count = Post.objects.count()
        # Открываем главную страницу
        page_content = self.authorized_client.get(self.index_url).content
        # Создаём ещё один пост
        yet_another_post = Post.objects.create(
            author=self.user,
            text='Прогресс неостановим',
        )
        # Проверяем, что количество постов в базе увеличилось
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Открываем главную страницу ещё раз
        cached_page_content = self.authorized_client.get(
            self.index_url
        ).content
        # Проверяем, что текст обновлённой страницы точно такой же,
        # как и до создания поста
        self.assertEqual(cached_page_content, page_content)
        # Чистим кеш
        cache.clear()
        # Обновляем главную страницу
        new_page = self.authorized_client.get(self.index_url).content
        # Проверяем, что текст страницы изменился
        self.assertNotEqual(cached_page_content, new_page)
        # Проверяем обратную последовательность. Удаляем пост.
        yet_another_post.delete()
        # Проверяем, что количество постов в базе уменьшилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Обновляем главную страницу
        cached_new_page = self.authorized_client.get(self.index_url).content
        # Проверяем, что текст страницы такой же, как и до удаления поста
        self.assertEqual(cached_new_page, new_page)
        # Чистим кеш
        cache.clear()
        # Обновляем страницу
        new_page_2 = self.authorized_client.get(self.index_url).content
        # Проверяем, что текст страницы изменился
        self.assertNotEqual(new_page_2, cached_new_page)

    def test_authorized_user_can_follow(self):
        """Проверка возможности подписки авторизованным пользователем."""
        # Проверяем возможность подписки
        follow_count = Follow.objects.count()
        # Подписываемся авторизованным пользователем на user2
        response = self.authorized_client.post(self.follow_url, follow=True)
        # Проверяем редирект
        self.assertRedirects(response, self.user2_url)
        # Проверяем, что подписок стало на 1 больше
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        # Проверяем, что есть подписка с правильными полями
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_authorized_user_can_unfollow(self):
        """Проверка возможности отписки авторизованным пользователем."""
        Follow.objects.create(user=self.user, author=self.user2)
        follow_count = Follow.objects.count()
        # Отписываемся от user2
        response = self.authorized_client.post(self.unfollow_url, follow=True)
        # Проверяем редирект
        self.assertRedirects(response, self.user2_url)
        # Проверяем, что подписок стало меньше
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        # Проверяем, что подписка с правильными полями исчезла
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_guest_client_cant_follow(self):
        follow_count = Follow.objects.count()
        response = self.guest_client.post(self.follow_url, follow=True)
        self.assertRedirects(
            response,
            reverse(
                'users:login'
            ) + '?next=/profile/user/follow/'
        )
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_post_of_followed_user_is_visible_for_follower(self):
        # user подписывается на user2
        self.authorized_client.post(self.follow_url, follow=True)
        # Запрашиваем страницу избранных авторов
        follower_page = self.authorized_client.get(self.follow_index_url)
        # Проверяем, что пост на странице с избранными авторами принадлежит
        # user2
        self.assertEqual(
            follower_page.context['page_obj'][0].author,
            self.user2
        )

        # user отписывается от user2
        self.authorized_client.post(self.unfollow_url, follow=True)
        # Запрашиваем страницу избранных авторов
        follower_page = self.authorized_client.get(self.follow_index_url)
        # Проверяем, что посты на страницу не выводятся,
        # т.к. подписок больше нет
        self.assertFalse(len(follower_page.context['page_obj']))
