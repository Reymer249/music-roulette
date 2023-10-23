from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from dotenv import load_dotenv
import os
import psycopg2
from .models import Parties
from .forms import RegisterForm


load_dotenv()
# Connect to the Azure PostgreSQL database server
con = psycopg2.connect(user=os.environ["DB_USER"], password=os.environ["DB_PASS"],
                       host=os.environ["DB_HOST"], database=os.environ["DB_NAME"],
                       port=os.environ["DB_PORT"])
cur = con.cursor()


def main_page(request):
    lobby_list = Parties.objects.all()
    lobby_list = [lobby.pid for lobby in lobby_list]
    context = {
        "lobby_list": lobby_list,
        "user": request.user
    }
    template = loader.get_template("main_page/index.html")
    return HttpResponse(template.render(context, request))


def sign_up(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = RegisterForm()

    return render(request, "registration/sign_up.html", {"form": form})


def create_party(request):
    if request.method == "POST":
        # Create a new Parties record
        party = Parties.objects.create()
        # Redirect to the lobby page
        return lobby_page(request, party.pid)
    return main_page(request)  # Render the main page with the button


def lobby_page(request, lobby_id):
    template = loader.get_template("lobby_page/index.html")
    context = {
        "lobby_id": lobby_id,
    }
    return HttpResponse(template.render(context, request))
