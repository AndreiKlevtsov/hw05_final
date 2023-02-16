from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..forms import PostForm, forms
from ..models import Group, Post, Comment

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем тестовый пост и группу."""
        super().setUpClass()
        cls.test_image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test_image.gif',
            content=cls.test_image,
            content_type='image/gif'
        )
        cls.author = User.objects.create(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        """Создаем клиент гостя и зарегистрированного пользователя."""
        self.auth_client = Client()
        self.auth_client.force_login(self.author)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def post_context(self, page_context):
        """Метод для проверки контекста поста на страницах."""
        if 'page_obj' in page_context:
            post = page_context['page_obj'][0]
        else:
            post = page_context['post']
        self.assertEqual(self.post.image, post.image)
        self.assertEqual(self.author, post.author)
        self.assertEqual(self.post.text, post.text)
        self.assertEqual(self.group, post.group)
        self.assertEqual(self.post.pk, post.pk)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth_client.get(reverse('posts:index'))
        self.post_context(response.context)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id})
        )
        self.post_context(response.context)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        self.post_context(response.context)
        self.assertEqual(group, self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username})
        )
        profile = response.context['author']
        self.post_context(response.context)
        self.assertEqual(profile, self.author)

    def test_create_edit_post_show_correct_context(self):
        """Шаблон post_create/edit сформирован с правильным контекстом."""
        url = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for url, slug in url:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context['form'].fields[value]
                        self.assertIsInstance(form_field, expected)
                        self.assertIsInstance(response.context['form'],
                                              PostForm)

    def test_auth_can_comment_post(self):
        """Только авторизованный пользователь может комментировать запись"""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.auth_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(Comment.objects.count(), 1)

    def test_post_appears_at_group(self):
        """Пост не появляется в другой группе."""
        Post.objects.create(
            author=self.author,
            text='Текстовый текст',
            group=self.group
        )
        test_group = Group.objects.create(
            title='Тест группа',
            slug='test-group-slug',
            description='Тестовое описание группы',
        )
        response = self.auth_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': test_group.slug}))

        self.assertEqual(len(response.context['page_obj']), 0)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile',
                    kwargs={'username': self.post.author}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'
            ),
        }
        for reverse_name, template in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_cache(self):
        """Кэш главной страницы работает корректно"""
        new_post = Post.objects.create(
            text='Тест кэша',
            author=self.author
        )
        response = self.auth_client.get(reverse('posts:index'))
        posts = response.content.decode('utf-8')
        cache_posts = response.content.decode('utf-8')
        self.assertEqual(posts, cache_posts)
        new_post.delete()
        response = self.auth_client.get(reverse('posts:index'))
        cache_posts = response.content.decode('utf-8')
        self.assertEqual(posts, cache_posts)
        cache.clear()
        response_clear = self.auth_client.get(reverse('posts:index'))
        cache_posts = response_clear.content.decode('utf-8')
        self.assertNotEqual(posts, cache_posts)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем записи и группу."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            [
                Post(
                    text=f'Тестовый пост + {i}', author=cls.author,
                    group=cls.group
                ) for i in range(settings.VISIBLE_POSTS + 3)
            ]
        )

    def setUp(self):
        """Создаем авторизованный клиент."""
        self.auth_client = Client()
        self.auth_client.force_login(self.author)
        cache.clear()

    def test_paginator(self):
        """Пагинатор выводит заданное количество записей."""
        urls_expected_posts = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}): (
                'posts/profile.html'),
        }
        for reverse_name in urls_expected_posts.keys():
            with self.subTest(reverse_name=reverse_name):
                response_posts1 = self.auth_client.get(reverse_name)
                response_posts2 = self.auth_client.get(
                    str(reverse_name) + '?page=2')
                self.assertEqual(len(response_posts1.context['page_obj']),
                                 settings.VISIBLE_POSTS)
                self.assertEqual(len(response_posts2.context['page_obj']),
                                 3)
                self.assertEqual(response_posts1.status_code, HTTPStatus.OK)
