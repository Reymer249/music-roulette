from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_page, name="main_page"),
    path("sign-up", views.sign_up, name="sign_up"),
    path("create_party/", views.create_party, name="create_party"),
    path("lobby/<int:lobby_id>/", views.lobby_page, name="lobby_page"),
]
