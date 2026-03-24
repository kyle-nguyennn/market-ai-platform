# System Overview

The Market AI Platform is a monorepo spanning three planes:

- **Data plane** — `services/dataset_platform` + `services/ingestion_worker`
- **Inference plane** — `services/inference_gateway`
- **Eval/control plane** — `services/eval_control_plane` + `services/training_worker`

See the individual service docs for component-level detail.
