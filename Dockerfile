# ─────────────────────────────────────────────────────────────
# STAGE 1: Build conda environment using micromamba
# ─────────────────────────────────────────────────────────────
FROM mambaorg/micromamba:1.5.6 AS builder

WORKDIR /app

COPY environment.yml .

RUN micromamba create -n phylocontext -f environment.yml --yes && \
    micromamba clean --all --yes

# ─────────────────────────────────────────────────────────────
# STAGE 2: Minimal Nextflow-compatible runtime
# ─────────────────────────────────────────────────────────────
FROM debian:bullseye-slim

# Install tools required by Nextflow for metrics and shell tasks
RUN apt-get update && \
    apt-get install -y \
      bash \
      procps \
      coreutils \
      gawk \
      grep \
      sed \
      findutils \
      util-linux \
      net-tools \
      tzdata \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy the phylocontext Conda environment
ENV CONDA_ENV_PATH=/opt/conda/envs/phylocontext
COPY --from=builder ${CONDA_ENV_PATH} ${CONDA_ENV_PATH}

# Copy scripts and link them into /usr/local/bin
WORKDIR /app/scripts
COPY scripts/ /app/scripts/

RUN chmod +x /app/scripts/get_annotations.py /app/scripts/get_info.py && \
    ln -s /app/scripts/get_annotations.py /usr/local/bin/get_annotations && \
    ln -s /app/scripts/get_info.py /usr/local/bin/get_info

# Activate Conda environment
ENV PATH=${CONDA_ENV_PATH}/bin:$PATH
ENV CONDA_DEFAULT_ENV=phylocontext
ENV PYTHONNOUSERSITE=1
