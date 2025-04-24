# Stage 1: Build the environment
FROM mambaorg/micromamba:1.5.6 AS builder

WORKDIR /app
COPY environment.yml .

RUN micromamba create -n phylocontext -f environment.yml --yes && \
    micromamba clean --all --yes

ENV PATH=/opt/conda/envs/phylocontext/bin:$PATH

# Stage 2: Final slim runtime
FROM debian:bullseye-slim

# Install CA certs for HTTPS validation and bash for debugging
RUN apt-get update && apt-get install -y bash ca-certificates && rm -rf /var/lib/apt/lists/*

# Setup conda enviorment 
ARG CONDA_ENV_NAME=phylocontext
ENV CONDA_ENV_PATH=/opt/conda/envs/$CONDA_ENV_NAME
COPY --from=builder $CONDA_ENV_PATH $CONDA_ENV_PATH

# Use the enviorment
ENV PATH=$CONDA_ENV_PATH/bin:$PATH
ENV CONDA_DEFAULT_ENV=$CONDA_ENV_NAME

# Set up WORKDIR
WORKDIR /app/scripts
COPY scripts/ /app/scripts/

# Make scripts executable and link into PATH
RUN chmod +x /app/scripts/get_annotations.py /app/scripts/get_info.py && \
    ln -s /app/scripts/get_annotations.py /usr/local/bin/get_annotations && \
    ln -s /app/scripts/get_info.py /usr/local/bin/get_info

# No ENTRYPOINT
CMD ["get_annotations", "--help"]
