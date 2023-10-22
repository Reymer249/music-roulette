from django.http import HttpResponse
from django.template import loader
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

LOCAL_DEV = os.environ['LOCAL_DEV'] == "True"

# Connect to the Azure PostgreSQL database server
if LOCAL_DEV:
    con = psycopg2.connect(user="postgres", password=os.environ["DBPASS"],
                           host="localhost", database="postgres")
else:
    con = psycopg2.connect(user=os.environ["DBUSER"], password=os.environ["DBPASS"],
                           host=os.environ["DBHOST"], database=os.environ["DBNAME"])
cur = con.cursor()


def main_page(request):
    lobby_list = [{"id": 12345}, {"id": 54321}, {"id": 23576}, {"id": 79840}]
    template = loader.get_template("main_page/index.html")
    context = {
        "lobby_list": lobby_list,
    }
    return HttpResponse(template.render(context, request))


def lobby_page(request, lobby_id):
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}]
    template = loader.get_template("lobby_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))

def question_page(request, lobby_id):
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}]
    template = loader.get_template("question_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))

def results_page(request, lobby_id):
    player_list = [{"id": 11, "name": "Natalka"}, {"id": 12, "name": "Ivan"}, {"id": 13, "name": "Max"}]
    template = loader.get_template("results_page/index.html")
    context = {
        "lobby_id": lobby_id,
        "player_list": player_list,
        "num_players": len(player_list),
    }
    return HttpResponse(template.render(context, request))