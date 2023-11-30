import time
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import UsersParties


@shared_task
def game_process(lobby_id, game_group_id):
    print("GAME STARTS")

    round_num = 5
    question_time = 5
    answer_time = 3
    ws_wait_time = 2
    start_wait_time = 6

    layer = get_channel_layer()
    player_list = UsersParties.objects.filter(party_id=lobby_id)
    round_cnt = 1
    scores = {player.id: 0 for player in player_list}

    # wait the users to establish a websocket connection while 5 sec game countdown ticks
    time.sleep(start_wait_time - ws_wait_time)

    async_to_sync(layer.group_send)(
        game_group_id,
        {
            "type": "init",
            "round_num": round_num,
            "player_ids": [player.user.id for player in player_list],
            "player_names": [player.user.name for player in player_list]
        }
    )

    # wait the rest of the 5 sec game countdown
    time.sleep(ws_wait_time)

    while round_cnt <= round_num:
        print("NEW ROUND")

        # TODO: select songs (Carlos)
        profile_links = {player.id: player.user.spotify_link for player in player_list}
        spotify_link = "https://open.spotify.com/embed/track/2UuOcNP8dU5nVq57ABxzIo?utm_source=generator"
        answer = 2  # the id of the selected song player
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

        # get answers from django cache
        answers = {player.id: cache.get(f"lobby_{lobby_id}_user_{player.id}_answer") for player in player_list}

        # grade answers
        for p, ans in answers.items():
            if ans == answer:
                scores[p] += 1

        print("SENDING CORRECT ANSWER")
        async_to_sync(layer.group_send)(
            game_group_id,
            {
                "type": "correct_ans",
                "answer": answer
            }
        )

        # wait for answer_time seconds for the users to discuss answers
        time.sleep(answer_time)

        round_cnt += 1

    print("SENDING RESULTS")
    async_to_sync(layer.group_send)(
        game_group_id,
        {
            "type": "game_results"
        }
    )

    print("GAME ENDS")
