from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutUrlTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists(self):
        """Проверяем статус страниц"""
        urls = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK
        }
        for url, status_code in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_code)
