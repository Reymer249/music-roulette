import time
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def game_process(lobby_id, lobby_group_id):
    print("GAME STARTS")
    round_cnt = 1
    round_num = 5
    question_time = 15
    layer = get_channel_layer()

    while round_cnt <= round_num:
        print("NEW ROUND")
        async_to_sync(layer.group_send)(
            lobby_group_id,
            {
                "type": "new_round",
                "round_num": round_cnt,
                "question_time": 15
            }
        )

        time.sleep(question_time)

        # TODO: get answers from django cache

        # TODO: grade answers
        scores = {"4": 37}  # pid: total score

        print("SENDING RESULTS")
        async_to_sync(layer.group_send)(
            lobby_group_id,
            {
                "type": ("round_results" if round_cnt < round_num else "game_results"),
                "round_num": round_cnt,
                "scores": scores
            }
        )

        round_cnt += 1

    print("GAME ENDS")
