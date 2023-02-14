from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем тестовый пост и группу."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.user_not_author = User.objects.create_user(username='Not_Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        """Создаем клиент гостя и зарегистрированного пользователя."""
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)
        self.authorized_not_author = Client()
        self.authorized_not_author.force_login(self.user_not_author)
        cache.clear()

    def test_urls_response_guest(self):
        """Проверяем статус страниц для пользователей."""
        url_list = [
            ('', self.client, HTTPStatus.OK),
            (f'/group/{self.group.slug}/', self.client, HTTPStatus.OK),
            (f'/profile/{self.user.username}/', self.client, HTTPStatus.OK),
            ('/create/', self.client, HTTPStatus.FOUND),
            ('/create/', self.authorized_not_author, HTTPStatus.OK),
            (f'/posts/{self.post.id}/', self.client, HTTPStatus.OK),
            (f'/posts/{self.post.id}/edit/', self.client, HTTPStatus.FOUND),
            (f'/posts/{self.post.id}/edit/', self.authorized_not_author,
             HTTPStatus.FOUND),
            (f'/posts/{self.post.id}/edit/', self.authorized_author,
             HTTPStatus.OK),
            ('f/unexisting_page/', self.client, HTTPStatus.NOT_FOUND),
        ]

        for url, client, status_code in url_list:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = [
            ('posts/index.html', ''),
            ('posts/group_list.html', f'/group/{self.group.slug}/'),
            ('posts/profile.html', f'/profile/{self.user.username}/'),
            ('posts/post_detail.html', f'/posts/{self.post.id}/'),
            ('posts/create_post.html', '/create/'),
            ('posts/create_post.html', f'/posts/{self.post.id}/edit/'),
            ('core/404.html', '/not_found/'),
            ('core/403.html', '/Custom CSRF/'),
        ]
        for template, url in templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)
