from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post, Comment

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем тестовый пост и группу."""
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_test = Group.objects.create(
            title='Новая группа для теста',
            slug='test-edit',
            description='Описание',
        )

    def setUp(self):
        """Создаем клиент гостя и зарегистрированного пользователя."""
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_valid_from_create_post(self):
        """Валидная форма создает новый пост и запись в базе данных."""
        gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image = SimpleUploadedFile(
            name='test_gif.gif',
            content=gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': image,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'posts:profile', args=(self.user_author,)
            ), HTTPStatus.FOUND
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.pk,
                image='posts/test_gif.gif'
            )
        )
        self.assertEqual(Post.objects.count(), 1)
        values = (
            (post.text, form_data['text']),
            (post.group.pk, form_data['group']),
            (image, form_data['image']),
            (post.author, self.user_author)
        )
        for param, expected in values:
            with self.subTest(param=param):
                self.assertEqual(param, expected)

    def test_cant_create_existing_slug(self):
        """Валидная форма редактирует пост."""
        gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        image = SimpleUploadedFile(
            name='test_gif.gif',
            content=gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user_author,
            text='Тестовый пост',
        )
        form_data = {
            'text': 'Edit text',
            'group': self.group_test.pk,
            'image': image.name
        }
        response = self.authorized_author.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post.pk}
            ),
            data=form_data,
            follow=True
        )
        response_not_author = self.client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post.pk}
            ),
            data=form_data,
            follow=True
        )
        post_edited = Post.objects.get(pk=post.pk)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post_edited.pk}
        ))
        self.assertRedirects(
            response_not_author, reverse(
                'users:login'
            ) + f'?next=/posts/{post.id}/edit/'
        )
        values = (
            (post_edited.text, form_data['text']),
            (post_edited.group.pk, form_data['group']),
            ('test_gif.gif', form_data['image']),
            (post_edited.author, self.user_author)
        )

        for param, expected in values:
            with self.subTest(param=param):
                self.assertEqual(param, expected)
                self.assertEqual(Post.objects.count(), 1)

    def test_form_create_comment(self):
        """Форма отправляет комментарий к записи"""
        Post.objects.create(
            text='Текст поста',
            group=self.group,
            author=self.user_author
        )
        form_data = {
            'text': 'Текст комментария',
        }
        post = Post.objects.get()
        self.authorized_author.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(Comment.objects.filter(**form_data).exists())
        self.assertEqual(Comment.objects.count(), 1)

