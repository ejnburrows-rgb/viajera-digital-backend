"""FastAPI backend for Viajera Digital."""

import os
import uuid
import asyncio
import json
from typing import Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from models import ProcessRequest
from pipeline import run_pipeline

jobs: Dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(os.environ.get("TEMP_DIR", "/tmp/viajera"), exist_ok=True)
    yield


app = FastAPI(
    title="Viajera Digital Backend",
    description="Cuban repentismo transcription and analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://viajera-digital-alpha.vercel.app,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "service": "viajera-digital-backend"}


@app.post("/api/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "processing",
        "progress": {"step": "pending", "percent": 0, "message": "En cola..."},
        "result": None, "error": None, "export_paths": None,
    }
    background_tasks.add_task(
        run_job, job_id, request.youtube_url,
        request.poet_a_name, request.poet_b_name
    )
    return {"job_id": job_id}


def run_job(job_id, youtube_url, poet_a_name, poet_b_name):
    def progress_callback(step, percent, message=""):
        if job_id in jobs:
            jobs[job_id]["progress"] = {"step": step, "percent": percent, "message": message}

    try:
        result = run_pipeline(job_id, youtube_url, poet_a_name, poet_b_name, progress_callback)
        export_paths = result.pop("_export_paths", {})
        jobs[job_id].update({
            "status": "complete", "result": result, "export_paths": export_paths,
            "progress": {"step": "complete", "percent": 100, "message": "Completado!"},
        })
    except Exception as e:
        msg = str(e)
        jobs[job_id].update({
            "status": "error",
            "error": {"status": "error", "step": jobs[job_id]["progress"].get("step", "unknown"),
                      "message": msg[:300], "detail": msg},
            "progress": {"step": "error", "percent": 0, "message": msg[:200]},
        })


@app.get("/api/progress/{job_id}")
async def progress_stream(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    async def event_generator():
        last_step = ""
        while True:
            if job_id not in jobs:
                break
            progress = jobs[job_id].get("progress", {})
            current_step = progress.get("step", "")
            if current_step != last_step or current_step == "transcribing":
                yield {"event": "progress", "data": json.dumps(progress)}
                last_step = current_step
            if current_step in ("complete", "error"):
                break
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())


@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    job = jobs[job_id]
    if job["status"] == "error":
        return JSONResponse(status_code=500, content=job["error"])
    if job["status"] != "complete":
        return JSONResponse(content={"status": "processing", "progress": job["progress"]})
    return JSONResponse(content=job["result"])


@app.get("/downloads/{job_id}/{fmt}")
async def download_file(job_id: str, fmt: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    job = jobs[job_id]
    if job["status"] != "complete" or not job.get("export_paths"):
        raise HTTPException(status_code=404, detail="Archivos no disponibles aun")

    format_map = {
        "pdf": ("pdf", "application/pdf"),
        "txt": ("txt", "text/plain; charset=utf-8"),
        "json": ("json", "application/json"),
    }
    if fmt not in format_map:
        raise HTTPException(status_code=400, detail="Formato no valido. Use: pdf, txt, json")

    key, media_type = format_map[fmt]
    filepath = job["export_paths"].get(key)
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Archivo {fmt} no encontrado")

    return FileResponse(filepath, media_type=media_type, filename=f"viajera_{job_id}.{key}")
