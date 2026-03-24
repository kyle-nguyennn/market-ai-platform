# System Overview

The Market AI Platform is a monorepo spanning three planes:

- **Data plane** — `services/dataset-platform` + `services/ingestion-worker`
- **Inference plane** — `services/inference-gateway`
- **Eval/control plane** — `services/eval-control-plane` + `services/training-worker`

See the individual service docs for component-level detail.
