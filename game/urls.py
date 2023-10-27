from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_page, name="main_page"),
    path("lobby/<int:lobby_id>/", views.lobby_page, name="lobby_page"),
    path("lobby/<int:lobby_id>/question/", views.question_page, name="question_page"),
    path("lobby/<int:lobby_id>/results/", views.results_page, name="results_page"),
    path("lobby/<int:lobby_id>/lobbyselect/", views.lobbyselect_page, name="lobbyselect_page"),
]
