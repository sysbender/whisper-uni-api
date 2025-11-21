import os
from pathlib import Path
from api.config import Config

def ensure_upload_dir():
    """Ensure upload directory exists."""
    Path(Config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def save_uploaded_file(file_content: bytes, filename: str, job_id: str) -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: File content bytes
        filename: Original filename
        job_id: Unique job identifier
    
    Returns:
        Path to saved file
    """
    ensure_upload_dir()
    
    file_ext = filename.split('.')[-1].lower()
    file_path = os.path.join(Config.UPLOAD_DIR, f"{job_id}.{file_ext}")
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return file_path

def delete_file(file_path: str):
    """Delete a file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)

