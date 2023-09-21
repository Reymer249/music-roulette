from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_page, name="main_page"),
    path("lobby/<int:lobby_id>/", views.lobby_page, name="lobby_page"),
]
