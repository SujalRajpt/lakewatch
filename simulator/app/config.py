import os
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    api_url: str = os.getenv("API_URL", "http://backend:8000/api/readings")

    simulated_day_seconds: int = 600

    reading_interval_simulated_minutes: int = 5

    missing_readings_enabled: bool = False
    duplicate_readings_enabled: bool = False
    malformed_payloads_enabled: bool = False
    out_of_order_enabled: bool = False
    delayed_events_enabled: bool = False
    anomalies_enabled: bool = False

    missing_reading_rate: float = 0.05
    duplicate_reading_rate: float = 0.02
    malformed_payload_rate: float = 0.02
    out_of_order_rate: float = 0.02
    delayed_event_rate: float = 0.02
    anomaly_rate: float = 0.02


config = SimulationConfig()
