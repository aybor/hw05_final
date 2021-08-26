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
        cls.group = PostModelTest.group
        cls.post = PostModelTest.post

        cls.verbose_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        cls.help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }

        cls.post_str = cls.post.text[:15]
        cls.group_str = cls.group.title

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        self.assertEqual(str(self.post), self.post_str)
        self.assertEqual(str(self.group), self.group_str)

    def test_post_model_verbose_names(self):
        """Проверяем, что у моделей корректно заданы verbose_names."""

        for value, expected in self.verbose_names.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name,
                    expected
                )

    def test_post_model_help_texts(self):
        """Проверяем, что у моделей корректно заданы help_texts."""

        for value, expected in self.help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text,
                    expected
                )
