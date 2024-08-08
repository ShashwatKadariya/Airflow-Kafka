from airflow.decorators import dag
from pendulum import datetime
from airflow.providers.apache.kafka.sensors.kafka import (
    AwaitMessageTriggerFunctionSensor,
)
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
import json
import uuid

PET_MOODS_NEEDING_A_WALK = ["sad", "happy"]
KAFKA_TOPIC = "topic_pet"


def listen_function(message, pet_moods_needing_a_walk=[]):
    message_content = json.loads(message.value())
    print(f"Message: {message_content}")
    pet_name = message_content["pet_name"]
    pet_mood_post_treat = message_content["pet_mood_post_treat"]
    final_treat = message_content["final_treat"]
    if final_treat:
        if pet_mood_post_treat in pet_moods_needing_a_walk:
            return pet_name, pet_mood_post_treat


def event_triggered_function(message, **context):
    pet_name = message[0]
    pet_mood_post_treat = message[1]
    print(
        f"Due to {pet_name} being in a {pet_mood_post_treat} mood, a walk is being initiated..."
    )
    TriggerDagRunOperator(
        trigger_dag_id="walking_my_pet",
        task_id=f"triggered_downstream_dag_{uuid.uuid4()}",
        wait_for_completion=True, 
        conf={
            "pet_name": pet_name
        },
        poke_interval=20,
    ).execute(context)

    print(f"The walk has concluded and {pet_name} is now happily taking a nap!")


@dag(
    start_date=datetime(2023, 4, 1),
    schedule="@continuous",
    max_active_runs=1,
    catchup=False,
    render_template_as_native_obj=True,
)
def listen_to_the_stream():
    AwaitMessageTriggerFunctionSensor(
        task_id="listen_for_mood",
        kafka_config_id="kafka_listener",
        topics=[KAFKA_TOPIC],
        apply_function="listen_to_the_stream.listen_function",
        poll_interval=5,
        poll_timeout=1,
        apply_function_kwargs={"pet_moods_needing_a_walk": PET_MOODS_NEEDING_A_WALK},
        event_triggered_function=event_triggered_function,
    )
listen_to_the_stream()
