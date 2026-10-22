
import json
import subprocess

from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel, Field


app = FastAPI(title="LakeWatch Spark Job Runner")


class AggregateRequest(BaseModel):
    columns: List[str] = Field(min_items=1)
    days: int = Field(ge=1, le=3650)


@app.post("/run-aggregation")
def run_aggregation(request: AggregateRequest):
    # Send arguments as separate command-line values, not shell text.
    command = [
        "/opt/spark/bin/spark-submit",
        "--master",
        "spark://spark-master:7077",
        "/workspace/jobs/data_lake/on_demand_aggregate.py",
        "--days",
        str(request.days),
        "--columns",
        ",".join(request.columns),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail="Spark aggregation timed out.",
        ) from exc

    if completed.returncode != 0:
        # Keep full diagnostics in the runner's logs.
        print(completed.stderr[-12000:])
        raise HTTPException(
            status_code=500,
            detail="Spark aggregation failed. Check the job-runner logs.",
        )

    # Spark logs also use stdout, so locate our explicit result marker.
    for line in reversed(completed.stdout.splitlines()):
        if line.startswith("LAKEWATCH_RESULT="):
            try:
                return json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="Spark returned an invalid result.",
                ) from exc

    print(completed.stdout[-12000:])
    raise HTTPException(
        status_code=500,
        detail="Spark completed without returning its result.",
    )
