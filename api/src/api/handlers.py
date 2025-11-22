from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from rq import Queue
from redis import Redis
from api.models import TranscribeResponse, JobStatus
from api.config import Config
from api.storage import save_uploaded_file
from typing import Optional
import uuid
import os

app = FastAPI(title="Universal Whisper Transcription API")

# Initialize Redis connection and queue
redis_conn = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
q = Queue(connection=redis_conn)

@app.post("/transcribe", response_model=TranscribeResponse)
async def upload_and_transcribe(
    file: UploadFile = File(...),
    engine: str = Form(...),
    language: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    """Upload audio and enqueue transcription job."""
    
    # Validate file format
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in Config.ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported format. Allowed: mp3, wav, m4a, flac")
    
    # Validate engine
    if engine not in ["whisperx", "timestamped"]:
        raise HTTPException(status_code=422, detail="Invalid engine. Must be 'whisperx' or 'timestamped'")
    
    # Read and validate file size
    content = await file.read()
    if len(content) > Config.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {Config.MAX_FILE_SIZE / (1024*1024)}MB")
    
    # Save file
    job_id = str(uuid.uuid4())
    file_path = save_uploaded_file(content, file.filename, job_id)
    
    # Enqueue job
    q.enqueue(
        'worker.tasks.transcribe',
        job_id,
        file_path,
        engine,
        language=language,
        model=model or "base",
        job_id=job_id
    )
    
    return TranscribeResponse(job_id=job_id)

@app.get("/status/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    """Query job status and retrieve results."""
    
    try:
        job = q.fetch_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = job.get_status()
        result = None
        error = None
        
        if status == "finished":
            result = job.result
        elif status == "failed":
            error = str(job.exc_info) if job.exc_info else "Unknown error"
        
        return JobStatus(
            job_id=job_id,
            status=status,
            result=result,
            error=error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job status: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        redis_conn.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": "disconnected", "error": str(e)}

