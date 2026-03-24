FROM mambaorg/micromamba:1.5-jammy
USER root
WORKDIR /app

COPY environment.yml pyproject.toml ./
RUN micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes

COPY libs/ libs/
COPY services/eval_control_plane/ services/eval_control_plane/

RUN micromamba run -n base pip install --no-deps -e .

ENV MAMBA_DOCKERFILE_ACTIVATE=1
CMD ["micromamba", "run", "-n", "base", "uvicorn", "services.eval_control_plane.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
