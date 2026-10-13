import os
import requests
import streamlit as st


SIMULATOR_URL = os.getenv(
    "SIMULATOR_URL",
    "http://localhost:9000",
)


st.set_page_config(
    page_title="LakeWatch Simulator",
    page_icon="🌊",
    layout="wide",
)


# ============================================================
# API HELPERS
# ============================================================


def get_api(endpoint):

    try:
        response = requests.get(
            f"{SIMULATOR_URL}{endpoint}",
            timeout=5,
        )

        if response.ok:
            return response.json()

        st.error(f"API error {response.status_code}: {response.text}")

    except requests.RequestException as error:
        st.error(f"Could not connect to simulator: {error}")

    return None


def post_api(endpoint, data):

    try:
        response = requests.post(
            f"{SIMULATOR_URL}{endpoint}",
            json=data,
            timeout=5,
        )

        if response.ok:
            return response.json()

        st.error(f"API error {response.status_code}: {response.text}")

    except requests.RequestException as error:
        st.error(f"Could not connect to simulator: {error}")

    return None


# ============================================================
# HEADER
# ============================================================


st.title("🌊 LakeWatch Simulator")

st.caption("Control individual lakes and simulate real-world sensor conditions.")


health = get_api("/health")


if health:
    st.success("🟢 Simulator Online")

else:
    st.error("🔴 Simulator Offline")


# ============================================================
# LAKE SELECTOR
# ============================================================


lakes = get_api("/simulation/lakes")


if not lakes:
    st.stop()


lake_map = {lake["lake_id"]: lake for lake in lakes}


selected_lake_id = st.selectbox(
    "🏞️ Select Lake",
    options=list(lake_map.keys()),
    format_func=lambda lake_id: f"{lake_map[lake_id]['name']} ({lake_id})",
)


selected_lake = lake_map[selected_lake_id]


st.caption(f"Profile: **{selected_lake['profile']}**")


# ============================================================
# LAKE STRESS
# ============================================================


st.divider()

st.header(f"🌡️ Lake Conditions — {selected_lake['name']}")


lake_data = get_api(f"/simulation/lakes/{selected_lake_id}")


if lake_data:
    current_stress = float(lake_data["stress_level"])

    stress = st.slider(
        "Stress Level",
        min_value=0.0,
        max_value=100.0,
        value=current_stress,
        step=1.0,
        key=f"stress_{selected_lake_id}",
    )

    if st.button(
        "Apply Stress",
        type="primary",
    ):
        result = post_api(
            f"/simulation/lakes/{selected_lake_id}/control",
            {
                "stress_level": stress,
            },
        )

        if result:
            st.success(f"{selected_lake_id} stress set to {stress:.0f}%")

            st.rerun()


# ============================================================
# DATA QUALITY
# ============================================================


st.divider()

st.header("⚠️ Data Quality")

st.caption(f"These settings apply only to **{selected_lake_id}**.")


behavior_response = get_api(f"/simulation/lakes/{selected_lake_id}/behaviors")


if behavior_response:
    behavior = behavior_response["behaviors"]

    # ========================================================
    # MISSING READINGS
    # ========================================================

    with st.container(border=True):
        st.subheader("Missing Readings")

        enabled = st.toggle(
            "Enable",
            value=behavior["missing_readings_enabled"],
            key=f"missing_enabled_{selected_lake_id}",
        )

        rate = st.slider(
            "Rate",
            0.0,
            1.0,
            float(behavior["missing_reading_rate"]),
            0.01,
            key=f"missing_rate_{selected_lake_id}",
        )

        if st.button(
            "Apply",
            key=f"missing_apply_{selected_lake_id}",
        ):
            post_api(
                f"/simulation/lakes/{selected_lake_id}/behaviors/control",
                {
                    "missing_readings_enabled": enabled,
                    "missing_reading_rate": rate,
                },
            )

            st.rerun()

    # ========================================================
    # DUPLICATES
    # ========================================================

    with st.container(border=True):
        st.subheader("Duplicate Readings")

        enabled = st.toggle(
            "Enable",
            value=behavior["duplicate_readings_enabled"],
            key=f"duplicate_enabled_{selected_lake_id}",
        )

        rate = st.slider(
            "Rate",
            0.0,
            1.0,
            float(behavior["duplicate_reading_rate"]),
            0.01,
            key=f"duplicate_rate_{selected_lake_id}",
        )

        if st.button(
            "Apply",
            key=f"duplicate_apply_{selected_lake_id}",
        ):
            post_api(
                f"/simulation/lakes/{selected_lake_id}/behaviors/control",
                {
                    "duplicate_readings_enabled": enabled,
                    "duplicate_reading_rate": rate,
                },
            )

            st.rerun()

    # ========================================================
    # MALFORMED PAYLOADS
    # ========================================================

    with st.container(border=True):
        st.subheader("Malformed Payloads")

        enabled = st.toggle(
            "Enable",
            value=behavior["malformed_payloads_enabled"],
            key=f"malformed_enabled_{selected_lake_id}",
        )

        rate = st.slider(
            "Rate",
            0.0,
            1.0,
            float(behavior["malformed_payload_rate"]),
            0.01,
            key=f"malformed_rate_{selected_lake_id}",
        )

        if st.button(
            "Apply",
            key=f"malformed_apply_{selected_lake_id}",
        ):
            post_api(
                f"/simulation/lakes/{selected_lake_id}/behaviors/control",
                {
                    "malformed_payloads_enabled": enabled,
                    "malformed_payload_rate": rate,
                },
            )

            st.rerun()

    # ========================================================
    # OUT OF ORDER
    # ========================================================

    with st.container(border=True):
        st.subheader("Out-of-Order Events")

        enabled = st.toggle(
            "Enable",
            value=behavior["out_of_order_enabled"],
            key=f"outorder_enabled_{selected_lake_id}",
        )

        rate = st.slider(
            "Rate",
            0.0,
            1.0,
            float(behavior["out_of_order_rate"]),
            0.01,
            key=f"outorder_rate_{selected_lake_id}",
        )

        if st.button(
            "Apply",
            key=f"outorder_apply_{selected_lake_id}",
        ):
            post_api(
                f"/simulation/lakes/{selected_lake_id}/behaviors/control",
                {
                    "out_of_order_enabled": enabled,
                    "out_of_order_rate": rate,
                },
            )

            st.rerun()

    # ========================================================
    # DELAYED EVENTS
    # ========================================================

    with st.container(border=True):
        st.subheader("Delayed Events")

        enabled = st.toggle(
            "Enable",
            value=behavior["delayed_events_enabled"],
            key=f"delayed_enabled_{selected_lake_id}",
        )

        rate = st.slider(
            "Rate",
            0.0,
            1.0,
            float(behavior["delayed_event_rate"]),
            0.01,
            key=f"delayed_rate_{selected_lake_id}",
        )

        if st.button(
            "Apply",
            key=f"delayed_apply_{selected_lake_id}",
        ):
            post_api(
                f"/simulation/lakes/{selected_lake_id}/behaviors/control",
                {
                    "delayed_events_enabled": enabled,
                    "delayed_event_rate": rate,
                },
            )

            st.rerun()

    # ========================================================
    # ANOMALIES
    # ========================================================

    with st.container(border=True):
        st.subheader("Sensor Anomalies")

        enabled = st.toggle(
            "Enable",
            value=behavior["anomalies_enabled"],
            key=f"anomaly_enabled_{selected_lake_id}",
        )

        rate = st.slider(
            "Rate",
            0.0,
            1.0,
            float(behavior["anomaly_rate"]),
            0.01,
            key=f"anomaly_rate_{selected_lake_id}",
        )

        if st.button(
            "Apply",
            key=f"anomaly_apply_{selected_lake_id}",
        ):
            post_api(
                f"/simulation/lakes/{selected_lake_id}/behaviors/control",
                {
                    "anomalies_enabled": enabled,
                    "anomaly_rate": rate,
                },
            )

            st.rerun()


# ============================================================
# CURRENT READING
# ============================================================


st.divider()

st.header("📡 Current Reading")


if st.button(
    "Generate Preview",
):
    response = get_api(f"/simulation/lakes/{selected_lake_id}/current-reading")

    if response:
        reading = response["reading"]

        cols = st.columns(3)

        metrics = [
            (
                "🌡️ Temperature",
                reading["temperature"],
                "°C",
            ),
            (
                "🧪 pH",
                reading["ph"],
                "",
            ),
            (
                "💧 Dissolved Oxygen",
                reading["dissolved_oxygen"],
                "mg/L",
            ),
            (
                "🌫️ Turbidity",
                reading["turbidity"],
                "NTU",
            ),
            (
                "⚡ Conductivity",
                reading["conductivity"],
                "µS/cm",
            ),
            (
                "🧪 Nitrate",
                reading["nitrate"],
                "mg/L",
            ),
        ]

        for index, (
            label,
            value,
            unit,
        ) in enumerate(metrics):
            with cols[index % 3]:
                st.metric(
                    label,
                    f"{value} {unit}",
                )

        with st.expander("Raw Reading"):
            st.json(response)


# ============================================================
# GLOBAL TRAFFIC
# ============================================================


st.divider()

st.header("🚀 Global Traffic")

st.caption("Concurrency and burst affect the simulator globally.")


# ============================================================
# CONCURRENCY
# ============================================================


concurrency = get_api("/simulation/concurrency")


if concurrency:
    with st.container(border=True):
        st.subheader("Concurrent Requests")

        enabled = st.toggle(
            "Enable concurrency",
            value=concurrency["enabled"],
        )

        mode = st.slider(
            "Requests per batch",
            min_value=1,
            max_value=100,
            value=min(
                int(concurrency["mode"]),
                100,
            ),
        )

        interval = st.slider(
            "Batch interval",
            min_value=0.1,
            max_value=30.0,
            value=float(concurrency["interval"]),
            step=0.1,
        )

        if st.button("Apply Concurrency"):
            post_api(
                "/simulation/concurrency/control",
                {
                    "enabled": enabled,
                    "mode": mode,
                    "interval": interval,
                },
            )

            st.rerun()


# ============================================================
# BURST
# ============================================================


burst = get_api("/simulation/burst")


if burst:
    with st.container(border=True):
        st.subheader("Burst Traffic")

        enabled = st.toggle(
            "Enable burst",
            value=burst["enabled"],
        )

        size = st.slider(
            "Burst size",
            min_value=1,
            max_value=1000,
            value=min(
                int(burst["size"]),
                1000,
            ),
        )

        interval = st.slider(
            "Burst interval",
            min_value=0.1,
            max_value=60.0,
            value=float(burst["interval"]),
            step=0.1,
        )

        if st.button("Apply Burst"):
            post_api(
                "/simulation/burst/control",
                {
                    "enabled": enabled,
                    "size": size,
                    "interval": interval,
                },
            )

            st.rerun()
