from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем тестовый пост и группу."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='guest')

    def setUp(self):
        """Создаем клиент гостя и зарегистрированного пользователя."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает нового пользователя и сохраняет базе
        данных. """
        form_data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'username': self.user.username,
            'email': self.user.email
        }
        response = self.authorized_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True,
        )
        users_count = User.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(User.objects.count(), users_count == 1)
        self.assertEqual(self.user.first_name, form_data['first_name'])
        self.assertEqual(self.user.last_name, form_data['last_name'])
        self.assertEqual(self.user.username, form_data['username'])
        self.assertEqual(self.user.email, form_data['email'])
