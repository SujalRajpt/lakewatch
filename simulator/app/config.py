import os
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    # --------------------------------------------------
    # Backend API
    # --------------------------------------------------

    api_url: str = os.getenv("API_URL", "http://backend:8000/api/readings")

    # --------------------------------------------------
    # Simulation timing
    # --------------------------------------------------

    simulated_day_seconds: int = 600
    reading_interval_simulated_minutes: int = 5

    # --------------------------------------------------
    # CONCURRENCY MODE
    # --------------------------------------------------

    # Enable / disable concurrency mode
    concurrency_enabled: bool = False

    # Number of normal sensor readings sent concurrently
    concurrency_mode: int = 1

    # Seconds between concurrent batches
    concurrency_interval: float = 2.0

    # --------------------------------------------------
    # BURST MODE
    # --------------------------------------------------

    # Enable / disable burst mode
    burst_enabled: bool = False

    # Total number of HTTP requests in one burst
    burst_size: int = 100

    # Seconds between bursts
    burst_interval: float = 10.0

    # --------------------------------------------------
    # Data-quality behaviors
    # --------------------------------------------------

    missing_readings_enabled: bool = False
    duplicate_readings_enabled: bool = False
    malformed_payloads_enabled: bool = False
    out_of_order_enabled: bool = False
    delayed_events_enabled: bool = False
    anomalies_enabled: bool = False

    # --------------------------------------------------
    # Probabilities
    # --------------------------------------------------

    missing_reading_rate: float = 0.05
    duplicate_reading_rate: float = 0.02
    malformed_payload_rate: float = 0.02
    out_of_order_rate: float = 0.02
    delayed_event_rate: float = 0.02
    anomaly_rate: float = 0.02


config = SimulationConfig()
