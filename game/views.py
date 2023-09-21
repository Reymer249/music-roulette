from django.http import HttpResponse
from django.template import loader
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

# Connect to the Azure PostgreSQL database server
con = psycopg2.connect(user=os.environ["DBUSER"], password=os.environ["DBPASS"],
                       host="musicroulette-server.postgres.database.azure.com",
                       port=5432, database="musicroulette-database")
cur = con.cursor()


def main_page(request):
    lobby_list = [{"id": 12345}, {"id": 54321}, {"id": 23576}, {"id": 79840}]
    template = loader.get_template("main_page/index.html")
    context = {
        "lobby_list": lobby_list,
    }
    return HttpResponse(template.render(context, request))


def lobby_page(request, lobby_id):
    template = loader.get_template("lobby_page/index.html")
    context = {
        "lobby_id": lobby_id,
    }
    return HttpResponse(template.render(context, request))
