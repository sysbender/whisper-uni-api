from redis import Redis
from worker.runners.whisperx import WhisperXRunner
from worker.runners.timestamped import TimestampedRunner
from worker.config import Config
import os
import logging

logger = logging.getLogger(__name__)

redis_conn = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

def get_runner(engine: str, model: str = "base"):
    """Factory to get appropriate runner."""
    if engine == "whisperx":
        return WhisperXRunner(model=model, device="cuda")
    elif engine == "timestamped":
        return TimestampedRunner(model=model, device="cuda")
    else:
        raise ValueError(f"Unknown engine: {engine}")

def transcribe(job_id: str, audio_path: str, engine: str, 
               language: str = None, model: str = "base"):
    """
    Main transcription task.
    
    Args:
        job_id: Unique job identifier
        audio_path: Path to uploaded audio file
        engine: Engine to use (whisperx, timestamped)
        language: Optional language code
        model: Model size (base, small, medium, large)
    
    Returns:
        dict: Transcription result with segments and timestamps
    """
    
    try:
        logger.info(f"Starting transcription job {job_id} with engine {engine}")
        
        # Validate audio file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Get runner and execute
        runner = get_runner(engine, model)
        result = runner.run(audio_path, language=language)
        
        # Convert TranscriptionResult to dict for JSON serialization
        result_dict = {
            "text": result["text"],
            "segments": [
                {
                    "id": seg["id"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "words": seg["words"]
                }
                for seg in result["segments"]
            ],
            "language": result["language"],
            "engine": result["engine"]
        }
        
        # Cleanup
        try:
            os.remove(audio_path)
            logger.info(f"Cleaned up audio file: {audio_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup audio file: {e}")
        
        logger.info(f"Completed transcription job {job_id}")
        return result_dict
    
    except Exception as e:
        logger.error(f"Transcription failed for job {job_id}: {str(e)}")
        raise Exception(f"Transcription failed: {str(e)}")

