from django.http import HttpResponse
from django.template import loader
import psycopg2

# Connect to the Azure PostgreSQL database server
# con = psycopg2.connect()
# cur = con.cursor()


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
