import asyncio
import copy

from datetime import datetime, timezone

import httpx

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import config
from .metadata import create_metadata
from .readings import (
    create_sensor_state,
    generate_reading,
)
from .control import lake_control

from .behaviors import (
    should_drop_reading,
    should_duplicate_reading,
    should_malformed_payload,
    should_out_of_order,
    should_delay_event,
    should_create_anomaly,
    create_malformed_payload,
    create_anomaly,
    create_out_of_order_timestamp,
)


app = FastAPI(
    title="LakeWatch Simulator Control API",
    description=("Control and inspect the LakeWatch sensor simulator."),
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------


class LakeControlRequest(BaseModel):
    stress_level: float = Field(
        ge=0, le=100, description="Lake stress level from 0 to 100"
    )


class BehaviorControlRequest(BaseModel):
    # Enable / disable behaviors

    missing_readings_enabled: bool | None = None

    duplicate_readings_enabled: bool | None = None

    malformed_payloads_enabled: bool | None = None

    out_of_order_enabled: bool | None = None

    delayed_events_enabled: bool | None = None

    anomalies_enabled: bool | None = None

    # Probability / rate

    missing_reading_rate: float | None = Field(
        default=None, ge=0, le=1, description="Probability between 0 and 1"
    )

    duplicate_reading_rate: float | None = Field(
        default=None, ge=0, le=1, description="Probability between 0 and 1"
    )

    malformed_payload_rate: float | None = Field(
        default=None, ge=0, le=1, description="Probability between 0 and 1"
    )

    out_of_order_rate: float | None = Field(
        default=None, ge=0, le=1, description="Probability between 0 and 1"
    )

    delayed_event_rate: float | None = Field(
        default=None, ge=0, le=1, description="Probability between 0 and 1"
    )

    anomaly_rate: float | None = Field(
        default=None, ge=0, le=1, description="Probability between 0 and 1"
    )


# --------------------------------------------------
# SIMULATOR STATE
# --------------------------------------------------

metadata = create_metadata()

sensor_states = []


for item in metadata:
    lake = item["lake"]
    sensor = item["sensor"]

    lake_control.initialize_lake(lake["lake_id"], 0)

    sensor_states.append(create_sensor_state(sensor, lake["profile"]))


# --------------------------------------------------
# BASIC HEALTH
# --------------------------------------------------


@app.get("/health")
def health():

    return {"status": "ok"}


# --------------------------------------------------
# LAKE CONTROL
# --------------------------------------------------


@app.get("/simulation/lakes")
def get_lakes():

    result = []

    for item in metadata:
        lake = item["lake"]

        result.append(
            {
                "lake_id": lake["lake_id"],
                "name": lake["name"],
                "profile": lake["profile"],
                "stress_level": (lake_control.get_stress_level(lake["lake_id"])),
            }
        )

    return result


@app.get("/simulation/lakes/{lake_id}")
def get_lake_control(lake_id: str):

    for item in metadata:
        lake = item["lake"]

        if lake["lake_id"] == lake_id:
            return {
                "lake_id": lake["lake_id"],
                "name": lake["name"],
                "profile": lake["profile"],
                "stress_level": (lake_control.get_stress_level(lake_id)),
            }

    raise HTTPException(status_code=404, detail="Lake not found")


@app.post("/simulation/lakes/{lake_id}/control")
def set_lake_control(lake_id: str, control: LakeControlRequest):

    try:
        lake_control.set_stress_level(lake_id, control.stress_level)

    except KeyError:
        raise HTTPException(status_code=404, detail="Lake not found")

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {
        "message": "Lake control updated",
        "lake_id": lake_id,
        "stress_level": (lake_control.get_stress_level(lake_id)),
    }


# --------------------------------------------------
# LAKE READING PREVIEW
# --------------------------------------------------


@app.get("/simulation/lakes/{lake_id}/current-reading")
def get_current_reading(lake_id: str):

    for state in sensor_states:
        if state["lake_id"] == lake_id:
            stress_level = lake_control.get_stress_level(lake_id)

            event_timestamp = datetime.now(timezone.utc)

            # Don't modify the real sensor state.
            preview_state = copy.deepcopy(state)

            reading = generate_reading(preview_state, event_timestamp, stress_level)

            return {
                "preview": True,
                "lake_id": lake_id,
                "stress_level": stress_level,
                "reading": reading,
            }

    raise HTTPException(status_code=404, detail="Lake not found")


# --------------------------------------------------
# DATA-QUALITY CONTROL
# --------------------------------------------------


@app.get("/simulation/behaviors")
def get_behavior_config():

    return {
        "missing_readings": {
            "enabled": (config.missing_readings_enabled),
            "rate": (config.missing_reading_rate),
        },
        "duplicate_readings": {
            "enabled": (config.duplicate_readings_enabled),
            "rate": (config.duplicate_reading_rate),
        },
        "malformed_payloads": {
            "enabled": (config.malformed_payloads_enabled),
            "rate": (config.malformed_payload_rate),
        },
        "out_of_order": {
            "enabled": (config.out_of_order_enabled),
            "rate": (config.out_of_order_rate),
        },
        "delayed_events": {
            "enabled": (config.delayed_events_enabled),
            "rate": (config.delayed_event_rate),
        },
        "anomalies": {
            "enabled": (config.anomalies_enabled),
            "rate": (config.anomaly_rate),
        },
    }


@app.post("/simulation/behaviors/control")
def set_behavior_config(control: BehaviorControlRequest):

    # ----------------------------------------------
    # ENABLE / DISABLE
    # ----------------------------------------------

    if control.missing_readings_enabled is not None:
        config.missing_readings_enabled = control.missing_readings_enabled

    if control.duplicate_readings_enabled is not None:
        config.duplicate_readings_enabled = control.duplicate_readings_enabled

    if control.malformed_payloads_enabled is not None:
        config.malformed_payloads_enabled = control.malformed_payloads_enabled

    if control.out_of_order_enabled is not None:
        config.out_of_order_enabled = control.out_of_order_enabled

    if control.delayed_events_enabled is not None:
        config.delayed_events_enabled = control.delayed_events_enabled

    if control.anomalies_enabled is not None:
        config.anomalies_enabled = control.anomalies_enabled

    # ----------------------------------------------
    # PROBABILITIES
    # ----------------------------------------------

    if control.missing_reading_rate is not None:
        config.missing_reading_rate = control.missing_reading_rate

    if control.duplicate_reading_rate is not None:
        config.duplicate_reading_rate = control.duplicate_reading_rate

    if control.malformed_payload_rate is not None:
        config.malformed_payload_rate = control.malformed_payload_rate

    if control.out_of_order_rate is not None:
        config.out_of_order_rate = control.out_of_order_rate

    if control.delayed_event_rate is not None:
        config.delayed_event_rate = control.delayed_event_rate

    if control.anomaly_rate is not None:
        config.anomaly_rate = control.anomaly_rate

    return {
        "message": ("Behavior configuration updated"),
        "config": {
            "missing_readings_enabled": config.missing_readings_enabled,
            "duplicate_readings_enabled": config.duplicate_readings_enabled,
            "malformed_payloads_enabled": config.malformed_payloads_enabled,
            "out_of_order_enabled": config.out_of_order_enabled,
            "delayed_events_enabled": config.delayed_events_enabled,
            "anomalies_enabled": config.anomalies_enabled,
            "missing_reading_rate": config.missing_reading_rate,
            "duplicate_reading_rate": config.duplicate_reading_rate,
            "malformed_payload_rate": config.malformed_payload_rate,
            "out_of_order_rate": config.out_of_order_rate,
            "delayed_event_rate": config.delayed_event_rate,
            "anomaly_rate": config.anomaly_rate,
        },
    }


# --------------------------------------------------
# SEND READING TO BACKEND
# --------------------------------------------------


async def send_reading(client, payload):

    try:
        response = await client.post(config.api_url, json=payload, timeout=10)

        print(
            f"[SENT] "
            f"{payload['sensor_id']} "
            f"seq={payload['sequence_number']} "
            f"status={response.status_code}"
        )

    except Exception as error:
        print(f"[ERROR] {payload['sensor_id']}: {error}")


# --------------------------------------------------
# SIMULATION LOOP
# --------------------------------------------------


async def simulation_loop():

    interval = (
        config.simulated_day_seconds
        / (24 * 60)
        * config.reading_interval_simulated_minutes
    )

    print("LakeWatch simulator started")

    print(f"Sending to: {config.api_url}")

    print(f"Interval: {interval:.2f} seconds")

    async with httpx.AsyncClient() as client:
        while True:
            event_timestamp = datetime.now(timezone.utc)

            for state in sensor_states:
                # ----------------------------------
                # MISSING READING
                # ----------------------------------

                if should_drop_reading(config):
                    print(f"[DROPPED] {state['sensor_id']}")

                    continue

                # ----------------------------------
                # NORMAL READING
                # ----------------------------------

                stress_level = lake_control.get_stress_level(state["lake_id"])

                payload = generate_reading(state, event_timestamp, stress_level)

                # ----------------------------------
                # OUT OF ORDER
                # ----------------------------------

                if should_out_of_order(config):
                    payload["event_timestamp"] = create_out_of_order_timestamp(
                        event_timestamp
                    ).isoformat()

                    print(
                        f"[OUT-OF-ORDER] "
                        f"{state['sensor_id']} "
                        f"seq={payload['sequence_number']}"
                    )

                # ----------------------------------
                # ANOMALY
                # ----------------------------------

                if should_create_anomaly(config):
                    payload = create_anomaly(payload)

                    print(
                        f"[ANOMALY] "
                        f"{state['sensor_id']} "
                        f"seq={payload['sequence_number']}"
                    )

                # ----------------------------------
                # MALFORMED PAYLOAD
                # ----------------------------------

                if should_malformed_payload(config):
                    payload = create_malformed_payload(payload)

                    print(
                        f"[MALFORMED] "
                        f"{state['sensor_id']} "
                        f"seq={payload['sequence_number']}"
                    )

                # ----------------------------------
                # DELAY
                # ----------------------------------

                if should_delay_event(config):
                    print(
                        f"[DELAYED] "
                        f"{state['sensor_id']} "
                        f"seq={payload['sequence_number']}"
                    )

                    await asyncio.sleep(2)

                # ----------------------------------
                # SEND
                # ----------------------------------

                await send_reading(client, payload)

                # ----------------------------------
                # DUPLICATE
                # ----------------------------------

                if should_duplicate_reading(config):
                    print(
                        f"[DUPLICATE] "
                        f"{state['sensor_id']} "
                        f"seq={payload['sequence_number']}"
                    )

                    await send_reading(client, payload)

            await asyncio.sleep(interval)


# --------------------------------------------------
# START SIMULATOR
# --------------------------------------------------


@app.on_event("startup")
async def startup_event():

    asyncio.create_task(simulation_loop())
