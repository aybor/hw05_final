import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from faker import Faker

from posts.models import Follow, Group, Post

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

        cls.user_username = 'auth'
        cls.user2_username = 'user'

        cls.test_group_title = 'Тестовая группа'
        cls.test_group_slug = 'test_slug'
        cls.test_group_description = 'Тестовое описание'

        cls.test_post_text = 'Тестовый текст'
        cls.test_post_group_text = 'Тестовый текст для поста с группой'

        cls.additional_group_title = 'YanGroup'
        cls.additional_group_slug = 'yangroup'
        cls.additional_group_description = 'Прогресс неостановим'
        cls.additional_post_text = 'Текст для дополнительной проверки'

        picture_name = 'small.gif'
        picture_content_type = 'image/gif'
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name=picture_name,
            content=cls.small_gif,
            content_type=picture_content_type
        )

        cls.user = User.objects.create_user(username=cls.user_username)
        cls.user2 = User.objects.create_user(username=cls.user2_username)

        cls.group = Group.objects.create(
            title=cls.test_group_title,
            slug=cls.test_group_slug,
            description=cls.test_group_description,
        )

        posts = [
            Post(
                author=cls.user,
                text=cls.test_post_text,
                pub_date=random_time(),
            )
            for i in range(14)
        ]

        posts.extend(
            [
                Post(
                    author=cls.user,
                    text=cls.test_post_group_text,
                    image=cls.uploaded,
                    group=cls.group,
                    pub_date=random_time(),
                ) for i in range(14)
            ]
        )
        posts.append(
            Post(
                author=cls.user2,
                text=cls.test_post_text,
            )
        )
        Post.objects.bulk_create(posts)

        cls.first_page_index_post_cnt = 10
        cls.second_page_index_post_cnt = 10
        cls.third_page_index_post_cnt = 9

        cls.first_page_group_post_cnt = 10
        cls.second_page_group_post_cnt = 4

        cls.first_page_profile_post_cnt = 10
        cls.second_page_profile_post_cnt = 10
        cls.third_page_profile_post_cnt = 8

        cls.add_second_page_url = '?page=2'
        cls.add_third_page_url = '?page=3'

        cls.page_obj_name = 'page_obj'
        cls.post_obj_name = 'post'
        cls.posts_cnt_name = 'author_posts_cnt'
        cls.edit_name = 'is_edit'

        post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': 1}
        )
        post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': 1}
        )

        cls.login_url = reverse('users:login')
        cls.post_create_url = reverse(
            'posts:post_create'
        )
        cls.index_url = reverse('posts:index')
        cls.group_url = reverse(
            'posts:group_posts',
            kwargs={'slug': 'test_slug'}
        )
        cls.auth_url = reverse(
            'posts:profile',
            kwargs={'username': cls.user_username}
        )
        cls.follow_index_url = reverse('posts:follow_index')

        cls.user2_url = reverse(
            'posts:profile',
            kwargs={'username': cls.user2_username}
        )
        cls.follow_url = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user2_username}
        )
        cls.unfollow_url = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user2_username}
        )

        cls.template_page_names = {
            cls.index_url: 'posts/index.html',
            cls.follow_index_url: 'posts/index.html',
            cls.group_url: 'posts/group_list.html',
            cls.auth_url: 'posts/profile.html',
            post_detail_url: 'posts/post_view.html',
            cls.post_create_url: 'posts/create_post.html',
            post_edit_url: 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):

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
        """
        first_page = self.authorized_client.get(self.index_url)
        second_page = self.authorized_client.get(
            self.index_url + self.add_second_page_url
        )
        third_page = self.authorized_client.get(
            self.index_url + self.add_third_page_url
        )

        pages = {
            first_page: self.first_page_index_post_cnt,
            second_page: self.second_page_index_post_cnt,
            third_page: self.third_page_index_post_cnt,
        }

        for page, length in pages.items():
            with self.subTest(page=page):
                self.assertEqual(
                    len(page.context[self.page_obj_name]),
                    length
                )
                for number in range(length):
                    with self.subTest(number=number):
                        post = page.context[self.page_obj_name][number]
                        self.assertIn(
                            post.author.username,
                            (self.user_username, self.user2_username)
                        )
                        if post.group:
                            self.assertEqual(
                                post.group.title,
                                self.test_group_title
                            )
                            self.assertEqual(
                                post.text,
                                self.test_post_group_text
                            )
                            self.assertEqual(
                                post.image,
                                Post.objects.get(pk=post.pk).image
                            )
                        else:
                            self.assertEqual(post.text, self.test_post_text)

                for number in range(length - 1):
                    with self.subTest(number=number):
                        self.assertGreaterEqual(
                            page.context[
                                self.page_obj_name
                            ][number].pub_date,
                            page.context[
                                self.page_obj_name
                            ][number + 1].pub_date
                        )

    def test_group_list_correct_context_with_paginator(self):
        """Проверяем, что:
        1) пагинатор сработал и выводит правильное
        количество постов на страницу;
        2) на страницах правильный контекст;
        3) посты на страницах отсортированы по возрастанию даты добавления.
        4) выведены только посты с указанной группой
        """

        first_page = self.authorized_client.get(self.group_url)
        second_page = self.authorized_client.get(
            self.group_url + self.add_second_page_url
        )

        pages = {
            first_page: self.first_page_group_post_cnt,
            second_page: self.second_page_group_post_cnt
        }

        for page, length in pages.items():
            with self.subTest(page=page):
                self.assertEqual(len(page.context[self.page_obj_name]), length)
                for number in range(length):
                    with self.subTest(number=number):
                        post = page.context[self.page_obj_name][number]
                        self.assertEqual(
                            post.author.username,
                            self.user_username
                        )
                        self.assertEqual(
                            post.group.title,
                            self.test_group_title
                        )
                        self.assertEqual(
                            post.text,
                            self.test_post_group_text
                        )
                        self.assertEqual(
                            post.image,
                            Post.objects.get(pk=post.pk).image
                        )

                for number in range(length - 1):
                    with self.subTest(number=number):
                        self.assertGreaterEqual(
                            page.context[
                                self.page_obj_name
                            ][number].pub_date,
                            page.context[
                                self.page_obj_name
                            ][number + 1].pub_date
                        )

    def test_profile_correct_context_with_paginator(self):
        """Проверяем, что:
        1) пагинатор сработал и выводит правильное
        количество постов на страницу;
        2) на страницах правильный контекст;
        3) посты на страницах отсортированы по возрастанию даты добавления.
        4) выведены только посты автора auth
        """
        # запоминаем содержание страниц
        first_page = self.authorized_client.get(self.auth_url)

        second_page = self.authorized_client.get(
            self.auth_url + self.add_second_page_url
        )

        third_page = self.authorized_client.get(
            self.auth_url + self.add_third_page_url
        )

        pages = {
            first_page: self.first_page_profile_post_cnt,
            second_page: self.second_page_profile_post_cnt,
            third_page: self.third_page_profile_post_cnt,
        }

        for page, length in pages.items():
            with self.subTest(page=page):
                self.assertEqual(len(page.context[self.page_obj_name]), length)
                for number in range(length):
                    with self.subTest(number=number):
                        post = page.context[self.page_obj_name][number]
                        self.assertEqual(
                            post.author.username,
                            self.user_username
                        )
                        if post.group:
                            self.assertEqual(
                                post.group.title,
                                self.test_group_title
                            )
                            self.assertEqual(
                                post.text,
                                self.test_post_group_text
                            )
                            self.assertEqual(
                                post.image,
                                Post.objects.get(pk=post.pk).image
                            )

                        else:
                            self.assertEqual(post.text, self.test_post_text)

                for number in range(length - 1):
                    with self.subTest(number=number):
                        self.assertGreaterEqual(
                            page.context[
                                self.page_obj_name
                            ][number].pub_date,
                            page.context[
                                self.page_obj_name
                            ][number + 1].pub_date
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
                    page.context[self.post_obj_name].text,
                    (
                        self.test_post_text,
                        self.test_post_group_text,
                    )
                )
                if post.group:
                    self.assertEqual(
                        page.context[self.post_obj_name].group,
                        post.group
                    )
                    self.assertEqual(
                        post.image,
                        Post.objects.get(pk=post.pk).image
                    )

                self.assertIn(
                    page.context[self.post_obj_name].author.username,
                    (self.user_username, self.user2_username)
                )

                self.assertEqual(
                    page.context[self.post_obj_name].pub_date,
                    post.pub_date
                )
                self.assertEqual(
                    page.context[self.posts_cnt_name],
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
                self.assertTrue(page.context[self.edit_name])
                self.assertIn(
                    page.context[self.post_obj_name].text,
                    (
                        self.test_post_group_text,
                        self.test_post_text,
                    )
                )
                if post.group:
                    self.assertEqual(
                        page.context[self.post_obj_name].group,
                        post.group
                    )

                self.assertIn(
                    page.context[self.post_obj_name].author.username,
                    (self.user_username, self.user2_username)
                )

                self.assertEqual(
                    page.context[self.post_obj_name].pub_date,
                    post.pub_date
                )

    def test_create_post_correct_form_and_creation(self):
        """Проверяем, что на страницу создания поста выводятся
        корректные поля.
        """

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        page = self.authorized_client.get(self.post_create_url)

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = page.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        yet_another_group = Group.objects.create(
            title=self.additional_group_title,
            slug=self.additional_group_slug,
            description=self.additional_group_description
        )

        yet_another_post = Post.objects.create(
            author=self.user,
            text=self.additional_post_text,
            group=yet_another_group,
            pub_date=random_time(),
        )

        post_page = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': yet_another_post.id}
            )
        )
        self.assertEqual(
            post_page.context[self.post_obj_name],
            yet_another_post
        )

        main_page = self.authorized_client.get(self.index_url)

        group_page = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': yet_another_group.slug}
            )
        )

        user_page = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user_username}
            )
        )

        for page in main_page, group_page, user_page:
            with self.subTest(page=page):
                self.assertEqual(
                    page.context[self.page_obj_name][0],
                    yet_another_post
                )

        self.assertNotIn(yet_another_post, self.group.posts.all())

    def test_index_cache(self):
        """Тестирование кеширования главной страницы."""
        posts_count = Post.objects.count()
        page_content = self.authorized_client.get(self.index_url).content
        yet_another_post = Post.objects.create(
            author=self.user,
            text=self.additional_post_text,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        cached_page_content = self.authorized_client.get(
            self.index_url
        ).content
        self.assertEqual(cached_page_content, page_content)

        cache.clear()

        new_page = self.authorized_client.get(self.index_url).content
        self.assertNotEqual(cached_page_content, new_page)

        yet_another_post.delete()
        self.assertEqual(Post.objects.count(), posts_count)

        cached_new_page = self.authorized_client.get(self.index_url).content
        self.assertEqual(cached_new_page, new_page)

        cache.clear()

        new_page_2 = self.authorized_client.get(self.index_url).content
        self.assertNotEqual(new_page_2, cached_new_page)

    def test_authorized_user_can_follow(self):
        """Проверка возможности подписки авторизованным пользователем."""
        follow_count = Follow.objects.count()
        response = self.authorized_client.post(self.follow_url, follow=True)
        self.assertRedirects(response, self.user2_url)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
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
        response = self.authorized_client.post(self.unfollow_url, follow=True)
        self.assertRedirects(response, self.user2_url)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
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
            response, f'{self.login_url}?next={self.follow_url}')
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user2
            ).exists()
        )

    def test_post_of_followed_user_is_visible_for_follower(self):
        self.authorized_client.post(self.follow_url, follow=True)
        follower_page = self.authorized_client.get(self.follow_index_url)
        self.assertEqual(
            follower_page.context[self.page_obj_name][0].author,
            self.user2
        )

        self.authorized_client.post(self.unfollow_url, follow=True)
        follower_page = self.authorized_client.get(self.follow_index_url)
        self.assertFalse(len(follower_page.context[self.page_obj_name]))
