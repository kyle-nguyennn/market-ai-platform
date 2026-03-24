# Dataset API

Base URL: `http://localhost:8001`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/datasets` | List all dataset versions |
| POST | `/datasets/build` | Trigger a new dataset build |
| GET | `/datasets/{name}/versions` | List versions for a dataset |
| GET | `/datasets/{name}/snapshot/{version}` | Fetch snapshot metadata |
| POST | `/features/materialize` | Materialize online features |
| GET | `/quality/reports/{dataset_version}` | Fetch quality report |
