from datetime import datetime, timezone

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.lake import Lake
from app.models.sensor import Sensor


LAKE_PROFILES = [
    {
        "lake_id": "LAKE-001",
        "name": "Lake Azure",
        "location": "Location-1",
    },
    {
        "lake_id": "LAKE-002",
        "name": "Lake Emerald",
        "location": "Location-2",
    },
    {
        "lake_id": "LAKE-003",
        "name": "Lake Silver",
        "location": "Location-3",
    },
    {
        "lake_id": "LAKE-004",
        "name": "Lake Crystal",
        "location": "Location-4",
    },
    {
        "lake_id": "LAKE-005",
        "name": "Lake Willow",
        "location": "Location-5",
    },
    {
        "lake_id": "LAKE-006",
        "name": "Lake Cedar",
        "location": "Location-6",
    },
    {
        "lake_id": "LAKE-007",
        "name": "Lake Orion",
        "location": "Location-7",
    },
    {
        "lake_id": "LAKE-008",
        "name": "Lake Lotus",
        "location": "Location-8",
    },
    {
        "lake_id": "LAKE-009",
        "name": "Lake Pearl",
        "location": "Location-9",
    },
    {
        "lake_id": "LAKE-010",
        "name": "Lake Sunset",
        "location": "Location-10",
    },
]


async def seed_database():
    async with SessionLocal() as session:
        async with session.begin():
            existing_lakes = set((await session.scalars(select(Lake.lake_id))).all())

            existing_sensors = set(
                (await session.scalars(select(Sensor.sensor_id))).all()
            )

            # Insert any missing predefined lakes first.
            for profile in LAKE_PROFILES:
                lake_id = profile["lake_id"]

                if lake_id not in existing_lakes:
                    session.add(
                        Lake(
                            lake_id=lake_id,
                            name=profile["name"],
                            location=profile["location"],
                        )
                    )

            # Ensure lakes exist before inserting sensors.
            await session.flush()

            # Insert any missing predefined sensors.
            for profile in LAKE_PROFILES:
                lake_id = profile["lake_id"]
                sensor_id = lake_id.replace("LAKE", "SENSOR")

                if sensor_id not in existing_sensors:
                    session.add(
                        Sensor(
                            sensor_id=sensor_id,
                            lake_id=lake_id,
                            model="AquaSense-X1",
                            firmware_version="1.0.0",
                            installation_date=datetime.now(timezone.utc),
                        )
                    )

    print("Database initialization complete: predefined lakes and sensors verified.")
