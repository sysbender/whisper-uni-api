1. API_SERVICE.md - FastAPI REST Service

Endpoints: POST /transcribe (upload audio), GET /status/{job_id} (query status)
Pydantic models for request/response validation
File storage and Redis queue integration
6 test cases covering success, validation errors, and edge cases
2. WORKER_SERVICE.md - RQ Background Worker

Base runner interface for engine abstraction
WhisperX and whisper-timestamped implementations
Task definition with job execution logic
7 test cases including mock runner tests, error handling, and subprocess failures
3. ENGINE_RUNNERS.md - Transcription Engine Runners

Unified output format (TranscriptionResult, TranscriptionSegment)
WhisperX runner with diarization support
Timestamped runner with VAD filtering
Output normalization to common schema
11 test cases covering both engines, error conditions, and edge cases
Key features across all docs:
✓ Concise, focused code examples
✓ Minimal but comprehensive test cases
✓ Configuration management
✓ Error handling strategies
✓ Dependencies clearly listed
✓ Deployment/running instructions
✓ Unified output format design