from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


def get_page(request, post_list):
    """Функция Paginator"""
    paginator = Paginator(post_list, settings.VISIBLE_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(settings.CACHE_TIME, key_prefix='index_page')
def index(request):
    """Отображает все добаленные записи"""
    posts = Post.objects.select_related('author', 'group')
    page_obj = get_page(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Отображает записи отсортированные по группам"""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = get_page(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Профиль пользователя"""
    author = get_object_or_404(
        User.objects.prefetch_related('posts', 'posts__group'),
        username=username
    )
    user = request.user.is_authenticated
    post_list = author.posts.all()
    page_obj = get_page(request, post_list)
    following = Post.objects.filter(author__following__user=user)
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Детали поста"""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group',), id=post_id
    )
    comments = post.comments.select_related('author',)
    form = CommentForm(
        request.POST or None
    )
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Добавление новой записи"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    form.save()
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    """Редактирование записи"""
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    context = {
        'is_edit': is_edit,
        'form': form,
    }
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    form.save()
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(
        request.POST or None
    )
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page(request, posts)
    context = {
        'page_obj': page_obj,
        'following': True
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    already_follow = Follow.objects.filter(user=request.user,
                                           author=author).exists()
    try:
        if author != user and not already_follow:
            Follow.objects.create(
                user=user,
                author=author
            )
            return redirect(
                'posts:follow_index'
            )
    except already_follow:
        return redirect(
            'posts:profile', username
        )
    post_list = author.posts.all()
    page_obj = get_page(request, post_list)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': True
    }
    return render(request, 'posts/profile.html', context)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.filter(user=user,
                              author=author).delete()
        return redirect('posts:index')
    return redirect(
        'posts:profile', username
    )
