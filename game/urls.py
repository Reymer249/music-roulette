from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_page, name="main_page"),
    path("login/", views.login_page, name="login_page"),
    path("create-party/", views.create_party, name="create_party"),
    path("lobby-select/", views.lobbyselect_page, name="lobbyselect_page"),
    path("lobby/<int:lobby_id>/", views.lobby_page, name="lobby_page"),
    path("lobby/<int:lobby_id>/game/", views.game_page, name="game_page"),
    path("lobby/<int:lobby_id>/results/", views.results_page, name="results_page"),
]
