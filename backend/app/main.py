from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_pagination import add_pagination

from app.api.routes import analytics, health, lakes, readings, sensors
from app.core.error_handlers import validation_exception_handler
from app.database.connection import initialize_database
from app.messaging.producer import create_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preserve existing database initialization and Kafka producer lifecycle.
    await initialize_database()

    producer = create_producer()
    await producer.start()
    app.state.kafka_producer = producer

    try:
        yield
    finally:
        await producer.stop()


app = FastAPI(
    title="LakeWatch API",
    description="Lake and sensor monitoring API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.include_router(health.router)
app.include_router(lakes.router)
app.include_router(sensors.router)
app.include_router(readings.router)
app.include_router(analytics.router)

add_pagination(app)
