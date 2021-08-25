import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа для формы',
            slug='test_slug_form',
            description='Тестовое описание для формы',
        )

        Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group1
        )
        cls.form = PostForm()

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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый тескт для формы',
            'group': self.group2.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел правильный редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            )
        )
        # Проверяем, что постов стало на 1 больше
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создан пост с правильными данными
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый тескт для формы',
                group=self.group2,
                author=self.user,
            ).exists()
        )
        # Проверяем, что пост не отностся ко второй группе
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый тескт для формы',
                group=self.group1,
            ).exists()
        )

    def test_post_edit(self):
        """Проверка возможности изменения поста."""
        posts_count = Post.objects.count()
        # Будем одновременно менять текст и группу
        form_data = {
            'text': 'Исправленный текст',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел правильный редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}
            )
        )
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что данные изменены правильно
        self.assertTrue(
            Post.objects.filter(
                text='Исправленный текст',
                group=self.group2.id,
                author=self.user,
            )
        )

    def test_not_create_post_for_guest_client(self):
        """Проверка отсутствия возможности создания поста неавторизованным
        клиентом.
        """
        # считаем количество постов
        posts_count = Post.objects.count()
        # создаём данные формы
        form_data = {
            'text': 'Тестовый тескт для гостевого клиента',
            'group': self.group1.id,
        }
        # делаем POST запрос от имени неавторизованного пользователя
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел редирект на страницу входа
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/create/'
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
            'text': 'Тестовый комментарий'
        }
        # Делаем POST запрос от имени авторизованного пользователя
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел правильный редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}
            )
        )
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что количество комментов изменилось
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        # Проверяем, что комментарий появляется на странице поста
        self.assertEqual(
            response.context['comments'][0].text,
            'Тестовый комментарий'
        )

    def test_not_add_comment_for_guest_client(self):
        """Проверка невозможности комментирования поста не авторизованным
        пользователем.
        """
        comments_count = Comment.objects.count()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        # Делаем POST запрос от имени неавторизованного пользователя
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        # Проверяем, что произошел редирект на страницу входа
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=/posts/1/comment/'
        )
        # Проверяем, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)

        # Проверяем, что количество комментов не изменилось
        self.assertEqual(Comment.objects.count(), comments_count)
