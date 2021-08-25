from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма для создания и изменения постов."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Форма для создания комментариев к постам."""
    class Meta:
        model = Comment
        fields = ('text',)
