from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group

        self.assertEqual(str(post), post.text[:15])
        self.assertEqual(str(group), group.title)

    def test_post_model_verbose_names(self):
        """Проверяем, что у моделей корректно заданы verbose_names."""
        post = PostModelTest.post

        verbose_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for value, expected in verbose_names.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_post_model_help_texts(self):
        """Проверяем, что у моделей корректно заданы help_texts."""
        post = PostModelTest.post

        help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }

        for value, expected in help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text,
                    expected
                )
