import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_username = 'auth'
        cls.test_title_group1 = 'Тестовая группа'
        cls.test_slug_group1 = 'test_slug'
        cls.test_description_group1 = 'Тестовое описание'
        cls.test_title_group2 = 'Тестовая группа для формы'
        cls.test_slug_group2 = 'test_slug_form'
        cls.test_description_group2 = 'Тестовое описание для формы'
        cls.test_text = 'Тестовый текст'
        cls.test_form_text = 'Тестовый тескт для формы'
        cls.corrected_form_text = 'Исправленный текст'
        cls.guest_form_text = 'Тескт для гостевого клиента'
        cls.test_comment_text = 'Тестовый комментарий'

        cls.user = User.objects.create_user(username=cls.user_username)

        cls.group1 = Group.objects.create(
            title=cls.test_title_group1,
            slug=cls.test_slug_group1,
            description=cls.test_description_group1,
        )
        cls.group2 = Group.objects.create(
            title=cls.test_title_group2,
            slug=cls.test_slug_group2,
            description=cls.test_description_group2,
        )

        cls.post_id = Post.objects.create(
            author=cls.user,
            text=cls.test_text,
            group=cls.group1
        ).pk

        cls.form = PostForm()

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

        cls.post_create_url = reverse('posts:post_create')
        cls.after_create_url = reverse(
            'posts:profile',
            kwargs={'username': cls.user_username}
        )
        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post_id}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post_id}
        )
        cls.login_url = reverse('users:login')
        cls.comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post_id})

        cls.add_next_create = f'?next={cls.post_create_url}'
        cls.add_next_comment = f'?next={cls.comment_url}'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаём авторизованного и гостевого клиента."""

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.guest_client = Client()

    def test_create_post(self):
        """Проверка возможности создания поста с картинкой."""

        posts_count = Post.objects.count()
        form_data = {
            'text': self.test_form_text,
            'group': self.group2.id,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            self.post_create_url,
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел правильный редирект
        self.assertRedirects(response, self.after_create_url)
        # Проверяем, что постов стало на 1 больше
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создан пост с правильными данными
        self.assertTrue(
            Post.objects.filter(
                text=self.test_form_text,
                group=self.group2,
                author=self.user,
            ).exists()
        )
        # Проверяем, что пост не отностся ко второй группе
        self.assertFalse(
            Post.objects.filter(
                text=self.test_form_text,
                group=self.group1,
            ).exists()
        )

    def test_post_edit(self):
        """Проверка возможности изменения поста."""
        posts_count = Post.objects.count()
        # Будем одновременно менять текст и группу
        form_data = {
            'text': self.corrected_form_text,
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            self.post_edit_url,
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел правильный редирект
        self.assertRedirects(response, self.post_detail_url)
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что данные изменены правильно
        self.assertTrue(
            Post.objects.filter(
                text=self.corrected_form_text,
                group=self.group2.id,
                author=self.user,
            )
        )

    def test_not_create_post_for_guest_client(self):
        """Проверка невозможности создания поста неавторизованным
        клиентом.
        """
        # считаем количество постов
        posts_count = Post.objects.count()
        # создаём данные формы
        form_data = {
            'text': self.guest_form_text,
            'group': self.group1.id,
        }
        # делаем POST запрос от имени неавторизованного пользователя
        response = self.guest_client.post(
            self.post_create_url,
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел редирект на страницу входа
        self.assertRedirects(
            response,
            self.login_url + self.add_next_create
        )
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment(self):
        """Проверка возможности комментирования поста авторизованным
        пользователем.
        """
        comments_count = Comment.objects.count()
        posts_count = Post.objects.count()
        form_data = {
            'text': self.test_comment_text
        }
        # Делаем POST запрос от имени авторизованного пользователя
        response = self.authorized_client.post(
            self.comment_url,
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел правильный редирект
        self.assertRedirects(
            response,
            self.post_detail_url
        )
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что количество комментов изменилось
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        # Проверяем, что комментарий появляется на странице поста
        self.assertEqual(
            response.context['comments'][0].text,
            self.test_comment_text
        )

    def test_not_add_comment_for_guest_client(self):
        """Проверка невозможности комментирования поста не авторизованным
        пользователем.
        """
        comments_count = Comment.objects.count()
        posts_count = Post.objects.count()
        form_data = {
            'text': self.test_comment_text
        }
        # Делаем POST запрос от имени неавторизованного пользователя
        response = self.guest_client.post(
            self.comment_url,
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел редирект на страницу входа
        self.assertRedirects(
            response,
            self.login_url + self.add_next_comment
        )
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)

        # Проверяем, что количество комментов не изменилось
        self.assertEqual(Comment.objects.count(), comments_count)
