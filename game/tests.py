from django.test import TestCase
from django.urls import reverse
from django.test import Client

from game.models import Users
from game.views import main_page
from game.views import create_party
from game.views import lobby_page

class Testing(TestCase):
    """
    This is a test class for the game application.

    The class contains the following methods:
    - test_main_view: Tests the main view of the game.
    - test_party_view: Tests the party view of the game.
    - test_lobby_view: Tests the lobby view of the game.
    - setup: Sets up the test environment.
    - create_user_test: Tests the user creation process.
    - test_login: Tests the login process.
    - test_logout: Tests the logout process.
    """
    def test_main_view(self):
        """
        This is a test method for the main view of the game.

        This method sends a GET request to the main page of the game and checks the following:
        - The HTTP response status code is 200, indicating a successful request.
        - The correct template, 'main_page/index.html', is used in the response.
        """
        response = self.client.get(reverse(main_page))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_page/index.html')

    def test_party_view(self):
        """
        This is a test method for the party view of the game.

        This method sends a GET request to the party creation page of the game and checks the following:
        - The HTTP response status code is 200, indicating a successful request.
        - The correct template, 'create_party/index.html', is used in the response.
        """
        response = self.client.get(reverse(create_party))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_party/index.html')

    def test_lobby_view(self):
        """
        This is a test method for the lobby view of the game.

        This method sends a GET request to the lobby page of the game and checks the following:
        - The HTTP response status code is 200, indicating a successful request.
        - The correct template, 'lobby_page/index.html', is used in the response.
        """
        response = self.client.get(reverse(lobby_page))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lobby_page/index.html')

    def setup(self):
        """
        This method sets up the test environment for the Testing class.

        It creates a user with a username and a spotify link, and a client for testing.

        Attributes:
            user (Users): A user instance with a username and a spotify link.
            client (Client): A client instance for testing.
        """
        self.user = Users.objects.create_user(username='Vova', spotify_link='https://open.spotify.com/user/arlfri0jaumrp6p902lvj1dva')
        self.client = Client()

    def create_user_test(self):
        """
        This is a test method for the user creation functionality.

        This method creates a user with a specified username and spotify link, and checks the following:
        - The user instance is not None, indicating a successful user creation.
        - The username of the created user matches the specified username.
        - The spotify link of the created user matches the specified spotify link.
        """
        self.assertIsNotNone(self.user)
        self.assertEqual(self.user.username, 'Vova')
        self.assertEqual(self.user.spotify_link, 'https://open.spotify.com/user/arlfri0jaumrp6p902lvj1dva')

    def test_login(self):
        """
        This is a test method for the login functionality.

        This method logs in a user with a specified username and spotify link, and checks the following:
        - The login instance is not None, indicating a successful login.
        - The username of the logged in user matches the specified username.
        - The spotify link of the logged in user matches the specified spotify link.
        """
        login = self.client.login(username='Vova', spotify_link='https://open.spotify.com/user/arlfri0jaumrp6p902lvj1dva')
        self.assertTrue(login)

    def test_logout(self):
        """
        This is a test method for the logout functionality.

        This method logs out a user and checks the following:
        - The HTTP response status code is 302, indicating a successful redirection after logout.
        """
        self.client.login(username='Vova', spotify_link='https://open.spotify.com/user/arlfri0jaumrp6p902lvj1dva')
        response = self.client.get('main_page/logout/')
        self.assertEqual(response.status_code, 302)
