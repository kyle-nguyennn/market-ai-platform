# Inference API

Base URL: `http://localhost:8002`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/score` | Score a single symbol |
| POST | `/score/batch` | Score a batch of symbols |
| POST | `/models/load` | Load or register a model |
| POST | `/models/promote` | Promote candidate to production |
| POST | `/models/canary` | Configure canary percentage |
| GET | `/health` | Health check |
