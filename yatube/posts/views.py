from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import pagination


@cache_page(20, key_prefix="index_page")
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group').all()
    page_obj = pagination(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = pagination(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    author_posts_cnt = post_list.count()
    page_obj = pagination(request, post_list)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'author_posts_cnt': author_posts_cnt,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_view(request, post_id):
    template = 'posts/post_view.html'
    post = get_object_or_404(Post, id=post_id)
    author_posts_cnt = post.author.posts.count()
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'author_posts_cnt': author_posts_cnt,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'

    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(
            reverse(
                'posts:profile',
                kwargs={'username': post.author}
            )
        )
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_id}
            )
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_id}
            )
        )
    context = {
        'is_edit': is_edit,
        'post': post,
        'form': form
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post(pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/index.html'
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    page_obj = pagination(request, post_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect(
            reverse(
                'posts:profile',
                kwargs={'username': username}
            )
        )
    author = get_object_or_404(User, username=username)
    Follow.objects.get_or_create(
        user=request.user,
        author=author
    )
    return redirect(
        reverse(
            'posts:profile',
            kwargs={'username': username}
        )
    )


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(
        Follow,
        author=author,
        user=request.user
    )
    follow.delete()
    return redirect(
        reverse(
            'posts:profile',
            kwargs={'username': username}
        )
    )
