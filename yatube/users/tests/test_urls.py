from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем тестовый пост и группу."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='guest')

    def setUp(self):
        """Создаем клиент гостя и зарегистрированного пользователя."""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_response_guest(self):
        """Проверяем статус страниц для гостя."""
        urls = {
            reverse('users:logout'): HTTPStatus.OK,
            reverse('users:signup'): HTTPStatus.OK,
            reverse('users:login'): HTTPStatus.OK,
            reverse('users:password_change'): HTTPStatus.FOUND,
            reverse('users:password_change_done'): HTTPStatus.FOUND,
            reverse('users:password_reset'): HTTPStatus.OK,
            reverse('users:password_reset_done'): HTTPStatus.OK,
            reverse(
                'users:password_reset_confirm',
                kwargs={'uidb64': 'MQ', 'token': '67r-c9ab02f0ecbcb1f1be4d'}
            ): HTTPStatus.OK,
            reverse('users:password_reset_complete'): HTTPStatus.OK
        }
        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_response_authorized(self):
        """Проверяем статус страниц для авторизованного пользователя."""
        urls = {
            reverse('users:password_change'): HTTPStatus.OK,
            reverse('users:password_change_done'): HTTPStatus.OK
        }
        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_names = {
            reverse('users:login'): 'users/login.html',
            reverse('users:signup'): 'users/signup.html',
            reverse(
                'users:password_change'
            ):
                'users/password_change_form.html',
            reverse(
                'users:password_change_done'
            ):
                'users/password_change_done.html',
            reverse(
                'users:password_reset'
            ):
                'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'
            ):
                'users/password_reset_done.html',
            reverse(
                'users:password_reset_confirm',
                kwargs={'uidb64': 'MQ', 'token': '67r-c9ab02f0ecbcb1f1be4d'}
            ):
                'users/password_reset_confirm.html',
            reverse(
                'users:password_reset_complete'
            ):
                'users/password_reset_complete.html',
            reverse('users:logout'): 'users/logged_out.html'
        }
        for reverse_name, template in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
