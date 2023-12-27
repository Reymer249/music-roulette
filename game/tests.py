from django.test import TestCase
from django.urls import reverse
from django.test import Client

from game.models import Users
from game.views import main_page
from game.views import create_party
from game.views import lobby_page

class Testing(TestCase):
    def test_main_view(self):
        response = self.client.get(reverse(main_page))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_page/index.html')

    def test_party_view(self):
        response = self.client.get(reverse(create_party))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_party/index.html')

    def test_lobby_view(self):
        response = self.client.get(reverse(lobby_page))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lobby_page/index.html')

    def setUp(self):
        self.user = Users.objects.create_user(username='Vova')
        self.client = Client()

    def create_user_test(self):
        self.assertIsNotNone(self.user)
        self.assertEqual(self.user.username, 'Vova')

    def test_login(self):
        login = self.client.login(username='Vova')
        self.assertTrue(login)

    def test_logout(self):
        self.client.login(username='Vova')
        response = self.client.get('main_page/logout/')
        self.assertEqual(response.status_code, 302)

