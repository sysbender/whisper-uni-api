"""
Main entry point for the Universal Whisper Transcription API.

This file can be used to run the API service directly.
For production, use uvicorn or gunicorn.
"""

from api.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

