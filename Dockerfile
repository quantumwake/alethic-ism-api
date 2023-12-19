# Stage 1: Base Image with Miniconda
FROM continuumio/miniconda3 as base

# Set the working directory
WORKDIR /app

ARG CONDA_ISM_CORE_PATH
ARG CONDA_ISM_DB_PATH
ARG GITHUB_REPO_URL

RUN git clone --depth 1 ${GITHUB_REPO_URL} repo
RUN mkdir -p /app/conda/env/local_channel

# copy the alethic-ism-core and alethic-ism-db conda packages
COPY ${CONDA_ISM_CORE_PATH} /app/conda/env/local_channel
COPY ${CONDA_ISM_DB_PATH} /app/conda/env/local_channel

# Move to the repository directory
WORKDIR /app/repo

# Force all commands to run in bash
SHELL ["/bin/bash", "--login", "-c"]

# Add the pytorch channel (required for apple silicon)
RUN conda config --add channels pytorch

# Initialize the conda environment specific to this build
RUN conda env create -f environment.yml

# Initialize conda in bash config files:
RUN conda init bash

# Activate the environment, and make sure it's activated:
RUN echo "conda activate alethic-ism-api" > ~/.bashrc

# Install ISM core directly instead, instead of environment.yml
RUN conda install /app/conda/env/local_channel/${CONDA_ISM_CORE_PATH}
RUN conda install /app/conda/env/local_channel/${CONDA_ISM_DB_PATH}

# Install Conda packages
RUN conda install psycopg2 \
    pydantic python-dotenv \
    pulsar-client \
    openai \
    tenacity \
    pyyaml \
    uvicorn \
    fastapi

# Stage 2: Application Image
FROM base as app

WORKDIR /app/repo

# Make port 80 available
EXPOSE 80

# Run Uvicorn when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

