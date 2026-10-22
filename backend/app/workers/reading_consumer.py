import asyncio
import base64
import json
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import OffsetAndMetadata, TopicPartition
from pydantic import ValidationError

from app.database.connection import SessionLocal
from app.models.reading import SensorReading
from app.schemas.reading import ReadingCreate
from app.services.idempotency import check_duplicate_event
from app.services.data_quality import (
    check_sequence_gap,
    check_out_of_order,
    check_delayed_reading,
    check_unexpected_interval,
    check_unexpected_gap,
)
from app.messaging.producer import create_producer


async def main():
    topic = os.getenv("KAFKA_TOPIC", "sensor-readings")

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"
        ),
        group_id=os.getenv(
            "KAFKA_CONSUMER_GROUP", "lakewatch-reading-processors"
        ),
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    dlq_producer = create_producer()

    try:
        await dlq_producer.start()
        await consumer.start()
        print("LakeWatch Kafka consumer started", flush=True)

        async for message in consumer:
            # 1. Decode and validate the incoming message.
            try:
                payload = json.loads(message.value.decode("utf-8"))

                if not isinstance(payload, dict):
                    raise ValueError("Message must be a JSON object")

                reading = ReadingCreate.model_validate(payload["reading"])

                received_raw = payload["received_at"]
                if not isinstance(received_raw, str):
                    raise ValueError("received_at must be a string")

                received_at = datetime.fromisoformat(
                    received_raw.replace("Z", "+00:00")
                )

                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=timezone.utc)

            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
                ValidationError,
                KeyError,
                TypeError,
                ValueError,
            ) as exc:
                # Preserve invalid messages for investigation.
                await dlq_producer.send_and_wait(
                    "sensor-readings-dlq",
                    key="invalid-message",
                    value={
                        "source_topic": message.topic,
                        "partition": message.partition,
                        "offset": message.offset,
                        "error": str(exc),
                        "raw_value_base64": base64.b64encode(
                            message.value
                        ).decode("ascii"),
                    },
                )

            else:
                # 2. Process the reading and flags atomically.
                async with SessionLocal() as db:
                    async with db.begin():
                        existing = await check_duplicate_event(db, reading)

                        if existing is None:
                            new_reading = SensorReading(
                                **reading.model_dump(),
                                received_at=received_at,
                            )

                            await check_sequence_gap(db, reading)
                            await check_out_of_order(db, reading)
                            await check_delayed_reading(
                                db, reading, received_at
                            )
                            await check_unexpected_interval(db, reading)
                            await check_unexpected_gap(db, reading)

                            db.add(new_reading)
                            print(
                                    f"Processed event_id={reading.event_id}",
                                    flush=True,
                                )

                # The DB transaction has succeeded, or a duplicate
                # was handled and its duplicate flag committed.

            # 3. Commit this message's offset only after successful handling.
            tp = TopicPartition(message.topic, message.partition)
            await consumer.commit({
                tp: OffsetAndMetadata(message.offset + 1, "")
            })

    finally:
        await consumer.stop()
        await dlq_producer.stop()


if __name__ == "__main__":
    asyncio.run(main())