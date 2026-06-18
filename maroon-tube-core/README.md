# Maroon Tube Core

> **Codex Reference:** §4.1 — Video Streaming Engine

Netflix/TikTok-style HLS video streaming. Deeply integrated into Safe Space (Reels-to-Instagram model).

## Pipeline

```
Upload (POST /api/v1/upload) → FFmpeg Transcode → HLS Segments → CDN Serve
                                        ↓
                                 Palantir Telemetry
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/upload` | POST | Upload a video file (multipart form) |
| `/stream/{hash}/playlist.m3u8` | GET | Stream HLS playlist |
| `/health` | GET | Service health check |

## Tech Stack
- **Language:** Go
- **Transcoding:** FFmpeg
- **Streaming:** HLS (HTTP Live Streaming)
- **Port:** 8080
