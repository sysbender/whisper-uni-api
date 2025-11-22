from pydantic import BaseModel, Field
from typing import Optional

class TranscribeRequest(BaseModel):
    engine: str = Field(..., pattern="^(whisperx|timestamped)$")
    language: Optional[str] = None
    model: Optional[str] = None

class TranscribeResponse(BaseModel):
    job_id: str
    status: str = "queued"

class JobStatus(BaseModel):
    job_id: str
    status: str  # queued, started, finished, failed
    result: Optional[dict] = None
    error: Optional[str] = None

