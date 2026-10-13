from sqlalchemy import select, desc
from app.models.reading import SensorReading
from app.models.flag import DataQualityFlag
from datetime import datetime, timedelta, timezone
#Call it from your endpoint 
#flags = await check_sequence_gap(db, SensorReading, reading)
async def check_sequence_gap(db, reading):
    query = (
        select(SensorReading)
        .where(SensorReading.sensor_id == reading.sensor_id)
        .order_by(desc(SensorReading.sequence_number))
        .limit(1)
    )

    result = await db.execute(query)
    previous = result.scalar_one_or_none()

    if previous is None:
        return []

    previous_seq = int(previous.sequence_number)
    current_seq = int(reading.sequence_number)

    if current_seq > previous_seq + 1:
        new_flag = DataQualityFlag(
            sensor_id=reading.sensor_id,
            event_id=reading.event_id,
            rule_code="SEQUENCE_GAP",
            details={
                "previous_sequence": previous_seq,
                "expected_sequence": previous_seq + 1,
                "observed_sequence": current_seq,
                "missing_from": previous_seq + 1,
                "missing_to": current_seq - 1,
            },
            status="OPEN",
        )

        db.add(new_flag)
        return [new_flag]

    return []


async def check_out_of_order(db, reading):
    query = (
        select(SensorReading)
        .where(SensorReading.sensor_id == reading.sensor_id)
        .order_by(desc(SensorReading.sequence_number))
        .limit(1)
    )

    result = await db.execute(query)
    previous = result.scalar_one_or_none()

    if previous is None:
        return []

    previous_seq = int(previous.sequence_number)
    current_seq = int(reading.sequence_number)

    if current_seq < previous_seq:
        new_flag = DataQualityFlag(
            sensor_id=reading.sensor_id,
            event_id=reading.event_id,
            rule_code="OUT_OF_ORDER",
            details={
                "previous_sequence": previous_seq,
                "observed_sequence": current_seq,
                "reason": "Sequence number is lower than the highest previously observed sequence",
            },
            status="OPEN",
        )

        db.add(new_flag)
        return [new_flag]

    return []


async def check_delayed_reading(db, reading, received_at):
    delay = received_at - reading.event_timestamp
    threshold = timedelta(seconds=15)

    if delay > threshold:
        new_flag = DataQualityFlag(
            sensor_id=reading.sensor_id,
            event_id=reading.event_id,
            rule_code="DELAYED_READING",
            details={
                "delay_seconds": delay.total_seconds(),
                "threshold_seconds": threshold.total_seconds(),
                "event_timestamp": reading.event_timestamp.isoformat(),
                "received_at": received_at.isoformat(),
            },
            status="OPEN",
        )

        db.add(new_flag)
        return [new_flag]

    return []

async def check_unexpected_interval(db, reading):
    query = (
        select(SensorReading)
        .where(SensorReading.sensor_id == reading.sensor_id)
        .order_by(desc(SensorReading.event_timestamp))
        .limit(1)
    )

    result = await db.execute(query)
    previous = result.scalar_one_or_none()

    if previous is None:
        return []

    previous_timestamp = previous.event_timestamp
    current_timestamp = reading.event_timestamp

    interval = current_timestamp - previous_timestamp
    threshold = timedelta(seconds=1.5)

    if timedelta(0) < interval < threshold:
        new_flag = DataQualityFlag(
            sensor_id=reading.sensor_id,
            event_id=reading.event_id,
            rule_code="UNEXPECTED_INTERVAL",
            details={
                "previous_event_timestamp": previous_timestamp.isoformat(),
                "current_event_timestamp": current_timestamp.isoformat(),
                "observed_interval_seconds": interval.total_seconds(),
                "minimum_expected_interval_seconds": threshold.total_seconds(),
            },
            status="OPEN",
        )

        db.add(new_flag)
        return [new_flag]

    return []


async def check_unexpected_gap(db, reading):
    query = (
        select(SensorReading)
        .where(SensorReading.sensor_id == reading.sensor_id)
        .order_by(desc(SensorReading.event_timestamp))
        .limit(1)
    )

    result = await db.execute(query)
    previous = result.scalar_one_or_none()

    if previous is None:
        return []

    previous_timestamp = previous.event_timestamp
    current_timestamp = reading.event_timestamp

    interval = current_timestamp - previous_timestamp
    threshold = timedelta(seconds=5)

    if interval > threshold:
        new_flag = DataQualityFlag(
            sensor_id=reading.sensor_id,
            event_id=reading.event_id,
            rule_code="UNEXPECTED_GAP",
            details={
                "previous_event_timestamp": previous_timestamp.isoformat(),
                "current_event_timestamp": current_timestamp.isoformat(),
                "observed_interval_seconds": interval.total_seconds(),
                "maximum_expected_interval_seconds": threshold.total_seconds(),
            },
            status="OPEN",
        )

        db.add(new_flag)
        return [new_flag]

    return []

