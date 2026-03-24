# Inference API

Base URL: `http://localhost:8002`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/score` | Score a single symbol |
| POST | `/batch_score` | Score a batch of symbols |
| GET | `/models` | List registered models |
| POST | `/models/promote` | Promote candidate to production |
| POST | `/models/canary` | Configure canary percentage |
| GET | `/health` | Health check |
