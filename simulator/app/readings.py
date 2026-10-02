import random
import uuid


def create_sensor_state(sensor, profile):

    return {
        "sensor_id": sensor["sensor_id"],
        "lake_id": sensor["lake_id"],
        "profile": profile,
        "sequence_number": 0,
        "temperature": random.uniform(22, 28),
        "ph": random.uniform(6.8, 7.8),
        "dissolved_oxygen": random.uniform(6, 9),
        "turbidity": random.uniform(1, 5),
        "conductivity": random.uniform(200, 500),
        "nitrate": random.uniform(1, 5),
    }


def apply_lake_character(state, stress_level):

    profile = state["profile"]

    intensity = stress_level / 100

    random_factor = random.uniform(0.85, 1.15)

    effect = intensity * random_factor

    if profile == "clean":
        state["turbidity"] += 1.5 * effect

        state["nitrate"] += 0.4 * effect

        state["conductivity"] += 20 * effect

        state["dissolved_oxygen"] -= 0.3 * effect

    elif profile == "sediment_heavy":
        state["turbidity"] += 12 * effect

        state["conductivity"] += 25 * effect

    elif profile == "nutrient_rich":
        state["nitrate"] += 7 * effect

        state["conductivity"] += 45 * effect

        state["dissolved_oxygen"] -= 1.2 * effect

    elif profile == "polluted":
        state["turbidity"] += 10 * effect

        state["nitrate"] += 8 * effect

        state["conductivity"] += 80 * effect

        state["dissolved_oxygen"] -= 2.5 * effect

        state["ph"] -= 0.8 * effect

    elif profile == "moderate":
        state["turbidity"] += 5 * effect

        state["nitrate"] += 3 * effect

        state["conductivity"] += 40 * effect

        state["dissolved_oxygen"] -= 0.8 * effect


def generate_reading(state, event_timestamp, stress_level):

    state["sequence_number"] += 1

    # Natural sensor variation
    state["temperature"] += random.uniform(-0.15, 0.15)

    state["ph"] += random.uniform(-0.03, 0.03)

    state["dissolved_oxygen"] += random.uniform(-0.1, 0.1)

    state["turbidity"] += random.uniform(-0.2, 0.2)

    state["conductivity"] += random.uniform(-5, 5)

    state["nitrate"] += random.uniform(-0.1, 0.1)

    # Lake-specific behavior
    apply_lake_character(state, stress_level)

    return {
        "event_id": str(uuid.uuid4()),
        "sensor_id": state["sensor_id"],
        "lake_id": state["lake_id"],
        "sequence_number": state["sequence_number"],
        "event_timestamp": (event_timestamp.isoformat()),
        "temperature": round(state["temperature"], 2),
        "ph": round(state["ph"], 2),
        "dissolved_oxygen": round(max(state["dissolved_oxygen"], 0), 2),
        "turbidity": round(max(state["turbidity"], 0), 2),
        "conductivity": round(max(state["conductivity"], 0), 2),
        "nitrate": round(max(state["nitrate"], 0), 2),
    }
