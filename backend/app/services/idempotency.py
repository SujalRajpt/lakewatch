from sqlalchemy import select

from app.models.reading import SensorReading
from app.models.flag import DataQualityFlag


async def check_duplicate_event(db, reading):
    query = select(SensorReading).where(
        SensorReading.event_id == reading.event_id
    )

    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing is None:
        return None

    # Compare the incoming payload with the stored reading.
    conflicts = {}

    fields_to_compare = [
        "sensor_id",
        "lake_id",
        "sequence_number",
        "event_timestamp",
        "ph",
        "temperature",
        "dissolved_oxygen",
        "turbidity",
    ]

    for field in fields_to_compare:
        incoming_value = getattr(reading, field, None)
        existing_value = getattr(existing, field, None)

        if incoming_value != existing_value:
            conflicts[field] = {
                "existing": str(existing_value),
                "incoming": str(incoming_value),
            }

    details = {
        "duplicate_event_id": reading.event_id,
        "conflicting_payload": bool(conflicts),
        "conflicts": conflicts,
    }

    new_flag = DataQualityFlag(
        reading_id=existing.id,
        sensor_id=reading.sensor_id,
        event_id=reading.event_id,
        rule_code="DUPLICATE_EVENT",
        details=details,
        status="OPEN",
    )

    db.add(new_flag)

    return existing