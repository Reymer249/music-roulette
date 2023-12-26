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
    """
    This function is a shared task that handles the game process.

    Parameters:
    lobby_id (int): The id of the lobby where the game is taking place.
    game_group_id (str): The id of the game group.

    The function initializes the game process, starts a countdown, and sends the initial game info to users.
    It also handles the game rounds, including question and answer times, and keeps track of the scores.
    The function continues to run until all players are ready.
    """
    print("GAME PROCESS STARTS")

    round_num = 5
    question_time = 10
    answer_time = 5
    start_wait_time = 5

    layer = get_channel_layer()
    player_list = [up.user for up in UsersParties.objects.filter(party_id=lobby_id)]
    round_cnt = 1
    scores = {player.id: 0 for player in player_list}
    played_songs = [""]

    ivan_id = None
    ivan = UsersParties.objects.filter(party_id=lobby_id, user__level=7)
    print(ivan.count())
    if ivan.count() >= 1:
        ivan_id = ivan.first().user.id

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
            "player_levels": [player.level for player in player_list]
        }
    )

    # wait the 5 sec game countdown
    time.sleep(start_wait_time)

    while round_cnt <= round_num:
        print("NEW ROUND")

        # select songs
        profile_token = {player.id: player.spotify_token for player in player_list}

        answer = random.choice(list(profile_token.keys()))

        print(f"PROFILE TOKEN: {profile_token}")
        print(f"ANSWER: {answer}")

        if answer == ivan_id:
            song_urls = ["https://open.spotify.com/track/36ezoymyNwbUSHSNiuI10A?si=51df8b6af35f4018",
                         "https://open.spotify.com/track/7fcIobA5JUkd90ad8y0cjO?si=7418dca95b814dbb",
                         "https://open.spotify.com/track/1MsLFY6sFtQmoVucRy0kF9?si=6c6f69ef6c394712",
                         "https://open.spotify.com/track/3ewQvXUYzZ817ROJaVI2va?si=691c18abd5b74e02",
                         "https://open.spotify.com/track/08ngkV9MwrLWjyjNc3GVPm?si=76b0c7cc78a34d93",
                         "https://open.spotify.com/track/3vxfjCT0toa4xCJ8yIAq01?si=95ff608142fd4ed4",
                         "https://open.spotify.com/track/3BF5XcGzssEL0Z5bP0a7OO?si=5e01d999f5b14de3"]
            weights = [73, 73, 7, 10, 10, 10, 42]
        else:
            service = get_spotipy_service(json.loads(profile_token[answer].replace("'", '"'))['access_token'])
            print(f"Token: {json.loads(profile_token[answer].replace("'", '"'))['access_token']}")

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
