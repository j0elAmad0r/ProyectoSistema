from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
ENTRYPOINT = BASE_DIR / "inicio.py"


class RunRequest(BaseModel):
    code: str = Field(..., min_length=1)
    mode: Literal["interpret", "compile"] = "interpret"


class RunResponse(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


app = FastAPI(title="Interprete API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Interprete API lista", "run": "POST /run"}


@app.post("/run", response_model=RunResponse)
def run_code(payload: RunRequest) -> RunResponse:
    if not ENTRYPOINT.exists():
        raise HTTPException(status_code=500, detail="No se encontro inicio.py")

    command = [sys.executable, str(ENTRYPOINT), payload.code, "--mode", payload.mode]

    try:
        completed = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired as exc:
        return RunResponse(
            success=False,
            stdout=exc.stdout or "",
            stderr="Timeout: el codigo tardo demasiado en ejecutarse.",
            exit_code=124,
        )

    return RunResponse(
        success=completed.returncode == 0,
        stdout=(completed.stdout or "").strip(),
        stderr=(completed.stderr or "").strip(),
        exit_code=completed.returncode,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
