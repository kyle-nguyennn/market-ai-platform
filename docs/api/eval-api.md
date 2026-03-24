# Eval API

Base URL: `http://localhost:8003`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/eval/runs` | Trigger a new eval run |
| GET | `/eval/runs/{id}` | Get eval run status and results |
| GET | `/eval/drift/alerts/{model_version}` | Get drift report for a model version |
| POST | `/eval/promotions/check` | Run promotion gate check |
| GET | `/eval/runs/{eval_run_id}/report` | Fetch full eval report |
