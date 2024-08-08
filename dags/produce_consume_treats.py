from airflow.decorators import dag, task
from pendulum import datetime
from airflow.providers.apache.kafka.operators.produce import ProduceToTopicOperator
from airflow.providers.apache.kafka.operators.consume import ConsumeFromTopicOperator
import json
import random


YOUR_NAME = "Shashwat"
YOUR_PET_NAME = "doggy"
NUMBER_OF_TREATS = 15

KAFKA_TOPIC = "topic_pet"


def prod_function(num_treats, pet_name):
    for i in range(num_treats):
        final_treat = False
        pet_mood_post_treat = random.choices(
            ["sad", "happy", "neutral", "excited"],
            weights=[1, 1, 1, 1],
            k=1,
        )[0]
        if i + 1 == num_treats:
            final_treat = True
        yield (
            json.dumps(i),
            json.dumps(
                {
                    "pet_name": pet_name,
                    "pet_mood_post_treat": pet_mood_post_treat,
                    "final_treat": final_treat,
                }
            ),
        )


# print consumed message contents to the log
def consume_function(message, name):
    key = json.loads(message.key())
    message_content = json.loads(message.value())
    pet_name = message_content["pet_name"]
    pet_mood_post_treat = message_content["pet_mood_post_treat"]
    print(
        f"Message #{key}: Hello {name}, your pet {pet_name} has consumed another treat and is now {pet_mood_post_treat}!"
    )


@dag(
    start_date=datetime(2023, 4, 1),
    schedule=None,
    catchup=False,
    render_template_as_native_obj=True,
)
def produce_consume_treats():
    @task
    def get_your_pet_name(pet_name=None):
        return pet_name

    @task
    def get_number_of_treats(num_treats=None):
        return num_treats

    @task
    def get_pet_owner_name(your_name=None):
        return your_name

    produce_treats = ProduceToTopicOperator(
        task_id="produce_treats",
        kafka_config_id="kafka_default",
        topic=KAFKA_TOPIC,
        producer_function=prod_function,
        producer_function_args=[get_number_of_treats(NUMBER_OF_TREATS)],
        producer_function_kwargs={"pet_name": get_your_pet_name(YOUR_PET_NAME)},
        poll_timeout=10,
    )

    consume_treats = ConsumeFromTopicOperator(
        task_id="consume_treats",
        kafka_config_id="kafka_default",
        topics=[KAFKA_TOPIC],
        apply_function=consume_function,
        apply_function_kwargs={"name": get_pet_owner_name(YOUR_NAME)},
        poll_timeout=20,
        max_messages=1000,
    )

    produce_treats >> consume_treats


produce_consume_treats()
