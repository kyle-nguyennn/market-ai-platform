-- Market AI Platform — initial schema

CREATE TABLE IF NOT EXISTS datasets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    version     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    artifact_uri TEXT,
    row_count   BIGINT,
    schema_hash TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS features (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,
    version     TEXT NOT NULL,
    definition  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quality_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_version TEXT NOT NULL,
    check_type      TEXT NOT NULL,
    status          TEXT NOT NULL,
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS models (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    version         TEXT NOT NULL,
    artifact_uri    TEXT,
    dataset_version TEXT,
    metrics         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS model_deployments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id    UUID REFERENCES models(id),
    slot        TEXT NOT NULL, -- 'production' | 'candidate'
    canary_pct  INT NOT NULL DEFAULT 0,
    deployed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_model  UUID REFERENCES models(id),
    candidate_model UUID REFERENCES models(id),
    dataset_version TEXT,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_metrics (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eval_run_id UUID REFERENCES eval_runs(id),
    model_id    UUID REFERENCES models(id),
    slice_key   TEXT,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS drift_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eval_run_id     UUID REFERENCES eval_runs(id),
    drift_type      TEXT NOT NULL,
    severity        TEXT NOT NULL,
    details         JSONB,
    resolved        BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS promotion_decisions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eval_run_id UUID REFERENCES eval_runs(id),
    decision    TEXT NOT NULL, -- 'approved' | 'blocked'
    reasons     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
