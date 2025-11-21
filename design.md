# Universal Whisper Transcription API

REST API for audio transcription using multiple Whisper-based engines.

## Overview

Microservice providing unified transcription interface with:
- **WhisperX** (with alignment, diarization)
- **whisper-timestamped** (lightweight, timestamped output)

**Stack:** FastAPI + Redis Queue (RQ) + GPU Workers  
**Deployment:** Docker Compose

---

## Functional Requirements

**Upload Endpoint**
- Accept audio files (mp3, wav, m4a, flac)
- Parameters: `engine` (whisperx | timestamped), `language` (optional), `model` (optional)
- Return: `job_id`

**Status Endpoint**
- Query job status (queued, started, finished, failed)
- Retrieve results once completed

**Execution**
- Long-running transcription in background workers (not API process)
- GPU acceleration support
- One job per GPU worker (enforced concurrency)

**Output**
- Unified JSON format with word and segment-level timestamps

---

## System Architecture

```
┌─────────────┐              POST /transcribe              ┌──────────────┐
│   FastAPI   │ ──────────────────────────────────────→ │  Redis Queue │
│    (API)    │ ←───────────────────────────────────── │    (RQ)      │
└─────────────┘              job_id                        └──────────────┘
      ▲                                                            │
      │                        GET /status/{job_id}               │
      └────────────────────────────────────────────  dequeued  ───┘
                                                           │
                                                           ▼
                                              ┌──────────────────────┐
                                              │   RQ Worker (GPU)    │
                                              │ - WhisperX runner    │
                                              │ - timestamped runner │
                                              └──────────────────────┘
```

---

## Component Design

**FastAPI Service**
- Accept file uploads, validate parameters
- Enqueue jobs into RQ, return job_id
- Query job status and retrieve results
- Manage temp file storage

**Redis Queue (RQ)**
- Store queued/completed jobs
- Maintain job state (queued → started → finished)
- Persist results
- Support retries

**RQ Worker**
- Execute transcription tasks one at a time
- Load and run WhisperX or whisper-timestamped CLI
- Normalize output to unified format
- Return results to Redis

**Engine Runners** (`worker/`)
- Abstract interface for each transcription engine
- Input: audio path, parameters
- Output: normalized JSON with timestamps

---

## Data Flow

1. **User uploads audio**
   - FastAPI saves file → enqueues job → returns job_id

2. **Worker picks up job**
   - Calls appropriate runner → produces JSON → stores result

3. **User polls /status/{job_id}**
   - API fetches job state and result

---

## Deployment

**Docker Compose Services:**
- `redis` - queue backend
- `api` - FastAPI application
- `worker` - RQ GPU worker(s)

**GPU Support:**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - capabilities: [gpu]
```

**Optional:**
- Multiple workers for multiple GPUs
- rq-dashboard for monitoring

---

## Error Handling

- Validate audio format/size at API
- Catch engine (CLI) failures in workers
- Worker-level timeouts via RQ
- Structured error responses (HTTP 400)
- Logging in worker containers

---

## Future Enhancements

- WebSocket streaming for real-time progress
- Authentication/authorization
- Model preloading for faster execution
- Multi-GPU orchestration
- Kubernetes deployment
- Additional engines (Whisper-large-v3-Turbo, distil-whisper)
