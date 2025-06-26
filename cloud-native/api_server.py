from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import os

app = FastAPI()

class UpdateRequest(BaseModel):
    project_id: str
    metadata_table: str
    job_run_table: str
    sleep_ms: Optional[int] = 1000
    max_workers: Optional[int] = 5

@app.post("/run")
async def run_update(req: UpdateRequest):
    try:
        env_path = "/tmp/.env"
        with open(env_path, "w") as f:
            f.write(f"PROJECT_ID={req.project_id}\n")
            f.write(f"METADATA_TABLE={req.metadata_table}\n")
            f.write(f"JOB_RUN_TABLE={req.job_run_table}\n")
            f.write(f"SLEEP_MSECONDS={req.sleep_ms}\n")
            f.write(f"MAX_PARALLEL_WORKERS={req.max_workers}\n")

        result = subprocess.run(
            ["python3", "update_column_descriptions.py", "--log"],
            env={**os.environ, "ENV_PATH": env_path},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/workspace"
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {"stdout": result.stdout, "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))