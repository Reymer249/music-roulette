import time
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import UsersParties
from .corlos import *
import json
import random


@shared_task
def game_process(lobby_id, game_group_id):
    print("GAME PROCESS STARTS")

    round_num = 3
    question_time = 5
    answer_time = 5
    start_wait_time = 6

    layer = get_channel_layer()
    player_list = [up.user for up in UsersParties.objects.filter(party_id=lobby_id)]
    round_cnt = 1
    scores = {player.id: 0 for player in player_list}

    while True:
        if [cache.get(f"lobby_{lobby_id}_user_{player.id}_ready") for player in player_list].count(True) == len(player_list):
            for player in player_list:
                cache.set(f"lobby_{lobby_id}_user_{player.id}_ready", None, 0)

            async_to_sync(layer.group_send)(
                game_group_id,
                {
                    "type": "start_countdown"
                }
            )

            break

        time.sleep(0.1)

    print("GAME STARTS")

    # send the init info to users

    async_to_sync(layer.group_send)(
        game_group_id,
        {
            "type": "init",
            "round_num": round_num,
            "player_ids": [player.id for player in player_list],
            "player_names": [player.name for player in player_list]
        }
    )

    # wait the 5 sec game countdown
    time.sleep(start_wait_time)

    while round_cnt <= round_num:
        print("NEW ROUND")

        # TODO: select songs (Carlos)
        profile_token = {player.id: player.spotify_token for player in player_list}
                        # Here I actually need: player.service for player.
                        # But im not sure if the 'service' can survive in the data base
                        # So maybe I just need to get the token and refresh the service always

        chosen_player = random.choice(list(profile_token.keys()))
        service = get_spotipy_service(json.loads(profile_token[chosen_player].replace("'", '"'))['access_token'])

        track_summaries = get_top_tracks(service) # + get_recent_tracks(service) + get_saved_tracks(service)
        song_urls = [summary['spotify_url'] for summary in track_summaries]
        weights = [summary['popularity'] for summary in track_summaries]

        picked_url = random.choices(song_urls, weights, k=1)[0]
        embedded_html = get_embedded_html(picked_url)

        spotify_link = "https://open.spotify.com/embed/track/2UuOcNP8dU5nVq57ABxzIo?utm_source=generator"

        answer = chosen_player
        # TODO: end select songs (Carlos)

        # send group the message about starting a new round
        async_to_sync(layer.group_send)(
            game_group_id,
            {
                "type": "new_round",
                "question_time": question_time,
                "answer_time": answer_time,
                "spotify_link": spotify_link
            }
        )

        # wait for question_time seconds to collect the answers from the users
        time.sleep(question_time)

        print("SENDING CORRECT ANSWER")
        async_to_sync(layer.group_send)(
            game_group_id,
            {
                "type": "correct_ans",
                "correct_ans": answer
            }
        )

        # get answers from django cache
        time.sleep(1)
        answers = {player.id: cache.get(f"lobby_{lobby_id}_user_{player.id}_answer") for player in player_list}

        # grade answers
        for p, ans in answers.items():
            if ans == f"p{answer}":
                scores[p] += 1

        for player in player_list:
            cache.set(f"lobby_{lobby_id}_user_{player.id}_answer", None, 0)

        cache.set(f"lobby_{lobby_id}_scores", scores)
        print(scores)

        # wait for answer_time seconds for the users to discuss answers
        time.sleep(answer_time - 1)

        round_cnt += 1

    print("SENDING RESULTS")
    async_to_sync(layer.group_send)(
        game_group_id,
        {
            "type": "game_results"
        }
    )

    print("GAME ENDS")
