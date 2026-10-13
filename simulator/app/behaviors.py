import random
from datetime import timedelta


def should_trigger(enabled, probability):
    return enabled and random.random() < probability


def should_drop_reading(behavior):
    return should_trigger(
        behavior["missing_readings_enabled"],
        behavior["missing_reading_rate"],
    )


def should_duplicate_reading(behavior):
    return should_trigger(
        behavior["duplicate_readings_enabled"],
        behavior["duplicate_reading_rate"],
    )


def should_malformed_payload(behavior):
    return should_trigger(
        behavior["malformed_payloads_enabled"],
        behavior["malformed_payload_rate"],
    )


def should_out_of_order(behavior):
    return should_trigger(
        behavior["out_of_order_enabled"],
        behavior["out_of_order_rate"],
    )


def should_delay_event(behavior):
    return should_trigger(
        behavior["delayed_events_enabled"],
        behavior["delayed_event_rate"],
    )


def should_create_anomaly(behavior):
    return should_trigger(
        behavior["anomalies_enabled"],
        behavior["anomaly_rate"],
    )


def create_malformed_payload(payload):

    malformed = payload.copy()

    behavior = random.choice(
        [
            "wrong_type",
            "missing_field",
            "null_value",
        ]
    )

    if behavior == "wrong_type":
        malformed["temperature"] = "not-a-number"

    elif behavior == "missing_field":
        malformed.pop("ph", None)

    elif behavior == "null_value":
        malformed["nitrate"] = None

    return malformed


def create_anomaly(payload):

    anomaly = payload.copy()

    parameter = random.choice(
        [
            "temperature",
            "ph",
            "dissolved_oxygen",
            "turbidity",
            "conductivity",
            "nitrate",
        ]
    )

    if parameter == "temperature":
        anomaly["temperature"] = random.choice([45.0, 50.0, 5.0])

    elif parameter == "ph":
        anomaly["ph"] = random.choice([2.5, 3.0, 11.0, 12.0])

    elif parameter == "dissolved_oxygen":
        anomaly["dissolved_oxygen"] = random.choice([0.2, 0.5, 15.0])

    elif parameter == "turbidity":
        anomaly["turbidity"] = random.uniform(
            30,
            60,
        )

    elif parameter == "conductivity":
        anomaly["conductivity"] = random.uniform(
            1000,
            2000,
        )

    elif parameter == "nitrate":
        anomaly["nitrate"] = random.uniform(
            20,
            50,
        )

    return anomaly


def create_out_of_order_timestamp(event_timestamp):

    return event_timestamp - timedelta(minutes=5)
