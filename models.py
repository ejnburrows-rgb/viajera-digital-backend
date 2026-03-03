"""Pydantic models for Viajera Digital backend."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    youtube_url: str = Field(..., description="YouTube URL of the repentismo event")
    poet_a_name: str = Field(default="Poeta A", description="Name of the first poet")
    poet_b_name: str = Field(default="Poeta B", description="Name of the second poet")


class Decima(BaseModel):
    number: int
    poet_id: str
    poet_name: str
    type: str = "controversia"
    lines: List[str] = Field(..., min_length=10, max_length=10)


class Top4Entry(BaseModel):
    rank: int = Field(..., ge=1, le=4)
    decima_number: int
    poet_id: str
    poet_name: str
    lines: List[str] = Field(..., min_length=10, max_length=10)
    analysis: str


class PoetInfo(BaseModel):
    id: str
    name: str
    decima_count: int = 0


class Downloads(BaseModel):
    pdf_url: str
    txt_url: str
    json_url: str


class ProcessResult(BaseModel):
    status: str = "complete"
    event_summary: str = ""
    technical_winner: str = ""
    total_decimas: int = 0
    duration_minutes: int = 0
    poets: List[PoetInfo] = []
    decimas: List[Decima] = []
    top_4: List[Top4Entry] = []
    downloads: Optional[Downloads] = None


class ProgressEvent(BaseModel):
    step: str
    percent: int = Field(..., ge=0, le=100)
    message: str = ""


class ErrorResponse(BaseModel):
    status: str = "error"
    step: str = ""
    message: str = ""
    detail: str = ""


class JobStatus(BaseModel):
    job_id: str
    status: str = "pending"
    progress: ProgressEvent = ProgressEvent(step="pending", percent=0, message="En cola...")
    result: Optional[ProcessResult] = None
    error: Optional[ErrorResponse] = None
