# Eval API

Base URL: `http://localhost:8003`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/eval-runs` | Trigger a new eval run |
| GET | `/eval-runs/{id}` | Get eval run status and results |
| GET | `/drift/{model_version}` | Get drift report for a model version |
| POST | `/promotions/check` | Run promotion gate check |
| GET | `/reports/{eval_run_id}` | Fetch full eval report |
