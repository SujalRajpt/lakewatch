
import json
import os

from aiokafka import AIOKafkaProducer


def create_producer() -> AIOKafkaProducer:
    return AIOKafkaProducer(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "kafka:9092",
        ),
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
    )
