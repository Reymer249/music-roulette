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
def game_process(lobby_id, game_group_id, ivan_id):
    print("GAME PROCESS STARTS")

    round_num = 3
    question_time = 5
    answer_time = 5
    start_wait_time = 5

    layer = get_channel_layer()
    player_list = [up.user for up in UsersParties.objects.filter(party_id=lobby_id)]
    round_cnt = 1
    scores = {player.id: 0 for player in player_list}
    played_songs = [""]

    if ivan_id is not None:
        ivan_times = random.sample(range(1, round_num + 1), 2)

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
            "player_names": [player.name for player in player_list],
            "ivan_id": ivan_id
        }
    )

    # wait the 5 sec game countdown
    time.sleep(start_wait_time)

    while round_cnt <= round_num:
        print("NEW ROUND")

        # select songs
        profile_token = {player.id: player.spotify_token for player in player_list}

        if ivan_id is not None and round_cnt in ivan_times:
            answer = ivan_id
        else:
            answer = random.choice(list(profile_token.keys()))

        if answer == ivan_id:
            song_urls = ["https://open.spotify.com/track/36ezoymyNwbUSHSNiuI10A?si=51df8b6af35f4018",
                         "https://open.spotify.com/track/7fcIobA5JUkd90ad8y0cjO?si=7418dca95b814dbb",
                         "https://open.spotify.com/track/1MsLFY6sFtQmoVucRy0kF9?si=6c6f69ef6c394712",
                         "https://open.spotify.com/track/3ewQvXUYzZ817ROJaVI2va?si=691c18abd5b74e02"]
            weights = [13, 15, 7, 11]
        else:
            service = get_spotipy_service(json.loads(profile_token[answer].replace("'", '"'))['access_token'])

            track_summaries = get_top_tracks(service) + get_recent_tracks(service) + get_saved_tracks(service)

            song_urls = [summary['spotify_url'] for summary in track_summaries]
            weights = [summary['popularity'] for summary in track_summaries]

        picked_url = ""
        while picked_url in played_songs:
            picked_url = random.choices(song_urls, weights, k=1)[0].replace("/track/", "/embed/track/")
        played_songs.append(picked_url)

        # send group the message about starting a new round
        async_to_sync(layer.group_send)(
            game_group_id,
            {
                "type": "new_round",
                "question_time": question_time,
                "answer_time": answer_time,
                "spotify_link": picked_url
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
