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
    description="Control and inspect the LakeWatch sensor simulator.",
)


# ============================================================
# REQUEST MODELS
# ============================================================


class LakeControlRequest(BaseModel):
    stress_level: float = Field(
        ge=0,
        le=100,
        description="Lake stress level from 0 to 100",
    )


class BehaviorControlRequest(BaseModel):
    # Enable / disable

    missing_readings_enabled: bool | None = None

    duplicate_readings_enabled: bool | None = None

    malformed_payloads_enabled: bool | None = None

    out_of_order_enabled: bool | None = None

    delayed_events_enabled: bool | None = None

    anomalies_enabled: bool | None = None

    # Rates

    missing_reading_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probability between 0 and 1",
    )

    duplicate_reading_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probability between 0 and 1",
    )

    malformed_payload_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probability between 0 and 1",
    )

    out_of_order_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probability between 0 and 1",
    )

    delayed_event_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probability between 0 and 1",
    )

    anomaly_rate: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Probability between 0 and 1",
    )


class ConcurrencyControlRequest(BaseModel):
    enabled: bool | None = None

    mode: int | None = Field(
        default=None,
        ge=1,
        le=10000,
        description="Number of requests sent concurrently",
    )

    interval: float | None = Field(
        default=None,
        ge=0.1,
        description="Seconds between concurrent batches",
    )


class BurstControlRequest(BaseModel):
    enabled: bool | None = None

    size: int | None = Field(
        default=None,
        ge=1,
        le=100000,
        description="Number of unique HTTP requests in each burst",
    )

    interval: float | None = Field(
        default=None,
        ge=0.1,
        description="Seconds between bursts",
    )


# ============================================================
# SIMULATOR STATE
# ============================================================


metadata = create_metadata()

sensor_states = []


# Default behavior for every lake

DEFAULT_BEHAVIOR_CONFIG = {
    "missing_readings_enabled": False,
    "duplicate_readings_enabled": False,
    "malformed_payloads_enabled": False,
    "out_of_order_enabled": False,
    "delayed_events_enabled": False,
    "anomalies_enabled": False,
    "missing_reading_rate": 0.05,
    "duplicate_reading_rate": 0.02,
    "malformed_payload_rate": 0.02,
    "out_of_order_rate": 0.02,
    "delayed_event_rate": 0.02,
    "anomaly_rate": 0.02,
}


# ============================================================
# INITIALIZE LAKES / SENSORS / BEHAVIORS
# ============================================================


lake_behavior_configs = {}


for item in metadata:
    lake = item["lake"]
    sensor = item["sensor"]

    lake_id = lake["lake_id"]

    # Stress starts at 0 for every lake

    lake_control.initialize_lake(
        lake_id,
        0,
    )

    # Create sensor state

    sensor_states.append(
        create_sensor_state(
            sensor,
            lake["profile"],
        )
    )

    # Every lake gets its own behavior configuration

    lake_behavior_configs[lake_id] = DEFAULT_BEHAVIOR_CONFIG.copy()


# ============================================================
# HELPER
# ============================================================


def get_lake_behavior(lake_id):

    behavior = lake_behavior_configs.get(lake_id)

    if behavior is None:
        raise HTTPException(
            status_code=404,
            detail="Lake not found",
        )

    return behavior


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
def health():

    return {"status": "ok"}


# ============================================================
# LAKE CONTROL
# ============================================================


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
                "stress_level": lake_control.get_stress_level(lake["lake_id"]),
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
                "stress_level": lake_control.get_stress_level(lake_id),
            }

    raise HTTPException(
        status_code=404,
        detail="Lake not found",
    )


@app.post("/simulation/lakes/{lake_id}/control")
def set_lake_control(
    lake_id: str,
    control: LakeControlRequest,
):

    try:
        lake_control.set_stress_level(
            lake_id,
            control.stress_level,
        )

    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Lake not found",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "message": "Lake control updated",
        "lake_id": lake_id,
        "stress_level": lake_control.get_stress_level(lake_id),
    }


# ============================================================
# CURRENT READING PREVIEW
# ============================================================


@app.get("/simulation/lakes/{lake_id}/current-reading")
def get_current_reading(lake_id: str):

    for state in sensor_states:
        if state["lake_id"] == lake_id:
            stress_level = lake_control.get_stress_level(lake_id)

            event_timestamp = datetime.now(timezone.utc)

            # Do not modify the real sensor state

            preview_state = copy.deepcopy(state)

            reading = generate_reading(
                preview_state,
                event_timestamp,
                stress_level,
            )

            return {
                "preview": True,
                "lake_id": lake_id,
                "stress_level": stress_level,
                "reading": reading,
            }

    raise HTTPException(
        status_code=404,
        detail="Lake not found",
    )


# ============================================================
# DATA QUALITY — ALL LAKES
# ============================================================


@app.get("/simulation/behaviors")
def get_all_behavior_configs():

    return lake_behavior_configs


# ============================================================
# DATA QUALITY — ONE LAKE
# ============================================================


@app.get("/simulation/lakes/{lake_id}/behaviors")
def get_lake_behavior_config(
    lake_id: str,
):

    behavior = get_lake_behavior(lake_id)

    return {
        "lake_id": lake_id,
        "behaviors": behavior.copy(),
    }


@app.post("/simulation/lakes/{lake_id}/behaviors/control")
def set_lake_behavior_config(
    lake_id: str,
    control: BehaviorControlRequest,
):

    behavior = get_lake_behavior(lake_id)

    # --------------------------------------------------------
    # ENABLE / DISABLE
    # --------------------------------------------------------

    if control.missing_readings_enabled is not None:
        behavior["missing_readings_enabled"] = control.missing_readings_enabled

    if control.duplicate_readings_enabled is not None:
        behavior["duplicate_readings_enabled"] = control.duplicate_readings_enabled

    if control.malformed_payloads_enabled is not None:
        behavior["malformed_payloads_enabled"] = control.malformed_payloads_enabled

    if control.out_of_order_enabled is not None:
        behavior["out_of_order_enabled"] = control.out_of_order_enabled

    if control.delayed_events_enabled is not None:
        behavior["delayed_events_enabled"] = control.delayed_events_enabled

    if control.anomalies_enabled is not None:
        behavior["anomalies_enabled"] = control.anomalies_enabled

    # --------------------------------------------------------
    # RATES
    # --------------------------------------------------------

    if control.missing_reading_rate is not None:
        behavior["missing_reading_rate"] = control.missing_reading_rate

    if control.duplicate_reading_rate is not None:
        behavior["duplicate_reading_rate"] = control.duplicate_reading_rate

    if control.malformed_payload_rate is not None:
        behavior["malformed_payload_rate"] = control.malformed_payload_rate

    if control.out_of_order_rate is not None:
        behavior["out_of_order_rate"] = control.out_of_order_rate

    if control.delayed_event_rate is not None:
        behavior["delayed_event_rate"] = control.delayed_event_rate

    if control.anomaly_rate is not None:
        behavior["anomaly_rate"] = control.anomaly_rate

    return {
        "message": "Lake behavior configuration updated",
        "lake_id": lake_id,
        "config": behavior.copy(),
    }


# ============================================================
# GLOBAL CONCURRENCY
# ============================================================


@app.get("/simulation/concurrency")
def get_concurrency_config():

    return {
        "enabled": config.concurrency_enabled,
        "mode": config.concurrency_mode,
        "interval": config.concurrency_interval,
    }


@app.post("/simulation/concurrency/control")
def set_concurrency_config(
    control: ConcurrencyControlRequest,
):

    if control.enabled is not None:
        config.concurrency_enabled = control.enabled

    if control.mode is not None:
        config.concurrency_mode = control.mode

    if control.interval is not None:
        config.concurrency_interval = control.interval

    return {
        "message": "Concurrency configuration updated",
        "config": {
            "enabled": config.concurrency_enabled,
            "mode": config.concurrency_mode,
            "interval": config.concurrency_interval,
        },
    }


# ============================================================
# GLOBAL BURST
# ============================================================


@app.get("/simulation/burst")
def get_burst_config():

    return {
        "enabled": config.burst_enabled,
        "size": config.burst_size,
        "interval": config.burst_interval,
    }


@app.post("/simulation/burst/control")
def set_burst_config(
    control: BurstControlRequest,
):

    if control.enabled is not None:
        config.burst_enabled = control.enabled

    if control.size is not None:
        config.burst_size = control.size

    if control.interval is not None:
        config.burst_interval = control.interval

    return {
        "message": "Burst configuration updated",
        "config": {
            "enabled": config.burst_enabled,
            "size": config.burst_size,
            "interval": config.burst_interval,
        },
    }


# ============================================================
# SEND READING
# ============================================================


async def send_reading(
    client,
    payload,
):

    try:
        response = await client.post(
            config.api_url,
            json=payload,
            timeout=10,
        )

        print(
            f"[SENT] "
            f"{payload['sensor_id']} "
            f"lake={payload['lake_id']} "
            f"seq={payload['sequence_number']} "
            f"event={payload['event_id']} "
            f"status={response.status_code}"
        )

    except Exception as error:
        print(
            f"[ERROR] "
            f"{payload['sensor_id']} "
            f"seq={payload['sequence_number']} "
            f"type={type(error).__name__} "
            f"error={repr(error)}"
        )


# ============================================================
# CONCURRENT BATCH
# ============================================================


async def send_concurrent_batch(
    client,
    payloads,
):

    tasks = [
        send_reading(
            client,
            payload,
        )
        for payload in payloads
    ]

    await asyncio.gather(*tasks)


# ============================================================
# BURST PAYLOADS
# ============================================================


def create_burst_payloads(
    burst_size,
):

    if not sensor_states:
        return []

    burst_payloads = []

    for i in range(burst_size):
        # Cycle through the available sensors.
        #
        # Example:
        # 300 requests / 10 sensors
        # = 30 readings per sensor

        state = sensor_states[i % len(sensor_states)]

        lake_id = state["lake_id"]

        # Get the current stress level for this lake

        stress_level = lake_control.get_stress_level(lake_id)

        # Generate a COMPLETELY NEW reading.
        #
        # generate_reading() creates:
        # - new event_id
        # - new sequence_number
        # - new sensor variation
        # - current lake stress effects

        payload = generate_reading(
            state,
            datetime.now(timezone.utc),
            stress_level,
        )

        burst_payloads.append(payload)

    return burst_payloads


# ============================================================
# SIMULATION LOOP
# ============================================================


async def simulation_loop():

    interval = (
        config.simulated_day_seconds
        / (24 * 60)
        * config.reading_interval_simulated_minutes
    )

    print("LakeWatch simulator started")

    print(f"Sending to: {config.api_url}")

    print(f"Normal interval: {interval:.2f} seconds")

    async with httpx.AsyncClient() as client:
        while True:
            event_timestamp = datetime.now(timezone.utc)

            payloads = []

            # =================================================
            # GENERATE READINGS
            # =================================================

            for state in sensor_states:
                lake_id = state["lake_id"]

                # Get THIS lake's behavior config

                behavior = lake_behavior_configs[lake_id]

                # ---------------------------------------------
                # MISSING READING
                # ---------------------------------------------

                if should_drop_reading(behavior):
                    print(f"[DROPPED] {state['sensor_id']} lake={lake_id}")

                    continue

                # ---------------------------------------------
                # STRESS
                # ---------------------------------------------

                stress_level = lake_control.get_stress_level(lake_id)

                # ---------------------------------------------
                # GENERATE READING
                # ---------------------------------------------

                payload = generate_reading(
                    state,
                    event_timestamp,
                    stress_level,
                )

                # ---------------------------------------------
                # OUT OF ORDER
                # ---------------------------------------------

                if should_out_of_order(behavior):
                    payload["event_timestamp"] = create_out_of_order_timestamp(
                        event_timestamp
                    ).isoformat()

                    print(
                        f"[OUT-OF-ORDER] "
                        f"{state['sensor_id']} "
                        f"lake={lake_id} "
                        f"seq={payload['sequence_number']}"
                    )

                # ---------------------------------------------
                # ANOMALY
                # ---------------------------------------------

                if should_create_anomaly(behavior):
                    payload = create_anomaly(payload)

                    print(
                        f"[ANOMALY] "
                        f"{state['sensor_id']} "
                        f"lake={lake_id} "
                        f"seq={payload['sequence_number']}"
                    )

                # ---------------------------------------------
                # MALFORMED
                # ---------------------------------------------

                if should_malformed_payload(behavior):
                    payload = create_malformed_payload(payload)

                    print(
                        f"[MALFORMED] "
                        f"{state['sensor_id']} "
                        f"lake={lake_id} "
                        f"seq={payload['sequence_number']}"
                    )

                # ---------------------------------------------
                # DELAYED
                # ---------------------------------------------

                if should_delay_event(behavior):
                    print(
                        f"[DELAYED] "
                        f"{state['sensor_id']} "
                        f"lake={lake_id} "
                        f"seq={payload['sequence_number']}"
                    )

                    await asyncio.sleep(2)

                payloads.append(payload)

            # =================================================
            # BURST MODE — GLOBAL
            #
            # Burst now generates UNIQUE events.
            # =================================================

            if config.burst_enabled:
                burst_payloads = create_burst_payloads(
                    config.burst_size,
                )

                print(
                    f"[BURST] Sending "
                    f"{len(burst_payloads)} "
                    f"unique requests concurrently"
                )

                await send_concurrent_batch(
                    client,
                    burst_payloads,
                )

                print(f"[BURST COMPLETE] {len(burst_payloads)} unique requests sent")

                await asyncio.sleep(config.burst_interval)

                continue

            # =================================================
            # CONCURRENCY MODE — GLOBAL
            # =================================================

            if config.concurrency_enabled:
                batch_size = config.concurrency_mode

                print(
                    f"[CONCURRENCY] "
                    f"Sending {len(payloads)} readings "
                    f"in batches of {batch_size}"
                )

                for i in range(
                    0,
                    len(payloads),
                    batch_size,
                ):
                    batch = payloads[i : i + batch_size]

                    print(f"[BATCH] {i + 1}-{i + len(batch)} ({len(batch)} requests)")

                    await send_concurrent_batch(
                        client,
                        batch,
                    )

                    if i + batch_size < len(payloads):
                        await asyncio.sleep(config.concurrency_interval)

            # =================================================
            # NORMAL MODE
            # =================================================

            else:
                for payload in payloads:
                    await send_reading(
                        client,
                        payload,
                    )

                    lake_id = payload["lake_id"]

                    behavior = lake_behavior_configs[lake_id]

                    # -----------------------------------------
                    # DUPLICATE
                    # -----------------------------------------

                    if should_duplicate_reading(behavior):
                        print(
                            f"[DUPLICATE] "
                            f"{payload['sensor_id']} "
                            f"lake={lake_id} "
                            f"seq={payload['sequence_number']}"
                        )

                        await send_reading(
                            client,
                            payload,
                        )

            # =================================================
            # NEXT CYCLE
            # =================================================

            await asyncio.sleep(interval)


# ============================================================
# START SIMULATOR
# ============================================================


@app.on_event("startup")
async def startup_event():

    asyncio.create_task(simulation_loop())
