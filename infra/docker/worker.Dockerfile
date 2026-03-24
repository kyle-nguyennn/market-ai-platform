FROM mambaorg/micromamba:1.5-jammy
USER root
WORKDIR /app

COPY environment.yml pyproject.toml ./
RUN micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes

COPY libs/ libs/
COPY services/ingestion_worker/ services/ingestion_worker/
COPY services/training_worker/ services/training_worker/

RUN micromamba run -n base pip install --no-deps -e .

ENV MAMBA_DOCKERFILE_ACTIVATE=1
CMD ["micromamba", "run", "-n", "base", "python", "-m", "services.ingestion_worker.main"]
