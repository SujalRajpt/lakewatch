from datetime import datetime, timezone


def create_metadata():

    lake_profiles = [
        {
            "lake_id": "LAKE-001",
            "name": "Lake Azure",
            "location": "Location-1",
            "profile": "clean",
        },
        {
            "lake_id": "LAKE-002",
            "name": "Lake Emerald",
            "location": "Location-2",
            "profile": "sediment_heavy",
        },
        {
            "lake_id": "LAKE-003",
            "name": "Lake Silver",
            "location": "Location-3",
            "profile": "nutrient_rich",
        },
        {
            "lake_id": "LAKE-004",
            "name": "Lake Crystal",
            "location": "Location-4",
            "profile": "polluted",
        },
        {
            "lake_id": "LAKE-005",
            "name": "Lake Willow",
            "location": "Location-5",
            "profile": "clean",
        },
        {
            "lake_id": "LAKE-006",
            "name": "Lake Cedar",
            "location": "Location-6",
            "profile": "sediment_heavy",
        },
        {
            "lake_id": "LAKE-007",
            "name": "Lake Orion",
            "location": "Location-7",
            "profile": "polluted",
        },
        {
            "lake_id": "LAKE-008",
            "name": "Lake Lotus",
            "location": "Location-8",
            "profile": "clean",
        },
        {
            "lake_id": "LAKE-009",
            "name": "Lake Pearl",
            "location": "Location-9",
            "profile": "nutrient_rich",
        },
        {
            "lake_id": "LAKE-010",
            "name": "Lake Sunset",
            "location": "Location-10",
            "profile": "moderate",
        },
    ]

    lakes = []

    for lake in lake_profiles:
        sensor = {
            "sensor_id": lake["lake_id"].replace("LAKE", "SENSOR"),
            "lake_id": lake["lake_id"],
            "model": "AquaSense-X1",
            "firmware_version": "1.0.0",
            "installation_date": datetime.now(timezone.utc).isoformat(),
        }

        lakes.append(
            {
                "lake": lake,
                "sensor": sensor,
            }
        )

    return lakes
