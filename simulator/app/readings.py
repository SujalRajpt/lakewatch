import random
import uuid


def create_sensor_state(sensor, profile):

    return {
        "sensor_id": sensor["sensor_id"],
        "lake_id": sensor["lake_id"],
        "profile": profile,
        "sequence_number": 0,
        # Baseline sensor values
        "temperature": random.uniform(22, 28),
        "ph": random.uniform(6.8, 7.8),
        "dissolved_oxygen": random.uniform(6, 9),
        "turbidity": random.uniform(1, 5),
        "conductivity": random.uniform(200, 500),
        "nitrate": random.uniform(1, 5),
    }


def apply_lake_character(state, stress_level, reading):
    profile = state["profile"]

    intensity = stress_level / 100

    random_factor = random.uniform(0.85, 1.15)

    effect = intensity * random_factor

    if profile == "clean":
        reading["turbidity"] += 1.5 * effect
        reading["nitrate"] += 0.4 * effect
        reading["conductivity"] += 20 * effect
        reading["dissolved_oxygen"] -= 0.3 * effect

    elif profile == "sediment_heavy":
        reading["turbidity"] += 12 * effect
        reading["conductivity"] += 25 * effect

    elif profile == "nutrient_rich":
        reading["nitrate"] += 7 * effect
        reading["conductivity"] += 45 * effect
        reading["dissolved_oxygen"] -= 1.2 * effect

    elif profile == "polluted":
        reading["turbidity"] += 10 * effect
        reading["nitrate"] += 8 * effect
        reading["conductivity"] += 80 * effect
        reading["dissolved_oxygen"] -= 2.5 * effect
        reading["ph"] -= 0.8 * effect

    elif profile == "moderate":
        reading["turbidity"] += 5 * effect
        reading["nitrate"] += 3 * effect
        reading["conductivity"] += 40 * effect
        reading["dissolved_oxygen"] -= 0.8 * effect


def generate_reading(state, event_timestamp, stress_level):

    state["sequence_number"] += 1

    # --------------------------------------------------------
    # Start from the sensor's baseline
    # --------------------------------------------------------

    reading = {
        "temperature": state["temperature"],
        "ph": state["ph"],
        "dissolved_oxygen": state["dissolved_oxygen"],
        "turbidity": state["turbidity"],
        "conductivity": state["conductivity"],
        "nitrate": state["nitrate"],
    }

    # --------------------------------------------------------
    # Natural sensor variation
    # --------------------------------------------------------

    reading["temperature"] += random.uniform(-0.15, 0.15)
    reading["ph"] += random.uniform(-0.03, 0.03)
    reading["dissolved_oxygen"] += random.uniform(-0.1, 0.1)
    reading["turbidity"] += random.uniform(-0.2, 0.2)
    reading["conductivity"] += random.uniform(-5, 5)
    reading["nitrate"] += random.uniform(-0.1, 0.1)

    # --------------------------------------------------------
    # Apply current lake conditions
    #
    # IMPORTANT:
    # This modifies only this reading.
    # It does NOT permanently modify state.
    # --------------------------------------------------------

    apply_lake_character(state, stress_level, reading)

    # --------------------------------------------------------
    # Return event
    # --------------------------------------------------------

    return {
        "event_id": str(uuid.uuid4()),
        "sensor_id": state["sensor_id"],
        "lake_id": state["lake_id"],
        "sequence_number": state["sequence_number"],
        "event_timestamp": event_timestamp.isoformat(),
        "temperature": round(reading["temperature"], 2),
        "ph": round(reading["ph"], 2),
        "dissolved_oxygen": round(max(reading["dissolved_oxygen"], 0), 2),
        "turbidity": round(max(reading["turbidity"], 0), 2),
        "conductivity": round(max(reading["conductivity"], 0), 2),
        "nitrate": round(max(reading["nitrate"], 0), 2),
    }
