# Alethic Instruction-Based State Machine (API)

The Alethic ISM API is the primary entry point for the Alethic ISM UI and the rest of the Alethic ISM platform. It provides a robust FastAPI-based web service with endpoints for managing processors, states, workflows, and more.

## System Overview

- **API Service**: Built with FastAPI, providing a well-organized RESTful API with OpenAPI documentation
- **Authentication**: Supports both Firebase and local authentication methods
- **Database**: Uses PostgreSQL for persistent storage via `ismdb.postgres_storage_class.PostgresDatabaseStorage`
- **Configuration**: Environment-based configuration using dotenv

## Core Components

- **Processors**: Engines that transform an input 'State' into an output 'State'
- **States**: Data structures that hold configuration and input/output information
- **Workflows**: Collections of processors and states that can be connected to form complex pipelines
- **Templates**: Reusable components for configuring states and processors
- **Projects**: Organizational units for grouping related workflows
- **Datasets**: Collections of data that can be processed by processors
- **Providers**: Service providers for language models and other processing capabilities
- **Users & Usage**: User management and usage tracking

## API Endpoints

The API provides the following endpoint groups:

- `/user`: User management endpoints
- `/usage`: Usage tracking endpoints
- `/project`: Project management endpoints
- `/workflow`: Workflow management endpoints 
- `/processor`: Processor management endpoints
- `/processor/state/route`: Processor state routing endpoints
- `/state`: State management endpoints
- `/session`: Session management endpoints
- `/provider`: Provider management endpoints
- `/filter`: Filter management endpoints
- `/template`: Template management endpoints
- `/monitor`: Monitoring endpoints
- `/streams`: Real-time state update streaming endpoints
- `/dataset`: Dataset management endpoints
- `/validate`: Validation endpoints

## Current Focus

- **Language Processors**: Our primary processors are for language processing – Anthropic and OpenAI – with more in development
- **Configurations**: Each processor uses a State, typically configured through StateConfigLM
- **State Configuration**: 
  - **StateConfig**: Includes basic settings like name, version, and storage engine
  - **StateConfigLM**: Handles user_templates, system_templates, model names, and provider names
- **Data Handling**: Processors manage datasets of key-value pairs, forming tabular datasets, with each pair processed according to the implemented Processor's functionality

## Deployment

### Docker

The application is containerized using Docker:
- Uses `uv` (Python package manager) on Debian base image
- Exposes port 80 for the API service
- Entry point script for container initialization
- Environment variables for configuration

### Kubernetes

Kubernetes deployment includes:
- deployment in the `alethic` namespace
- Secret management for configuration files and credentials
- Environment variables via Kubernetes secrets
- Volume mounts for routing configuration and Firebase credentials

## Prerequisites

- Python (versions >=3.10 and <=3.12)
- Conda (preferably miniconda)
- UV package manager (`pip install uv`)
- PostgreSQL database

## Getting Started

### Required Repositories (optional as it is already part of pypi)
```
git clone https://github.com/quantumwake/alethic-ism-core.git
git clone https://github.com/quantumwake/alethic-ism-db.git
```

### Building with Docker
```
./docker_build.sh -t krasaee/alethic-ism-api:local
```

## Release Process

### Create a new release tag
```shell
git tag -a v0.1.0 -m "Release v0.1.0"
```

### Push just that tag
```shell
git push origin v0.1.0
```

### Push all tags (optional- to push commits + tags)
```shell
git push --follow-tags
```

## License
Alethic ISM is under a DUAL licensing model, please refer to [LICENSE.md](LICENSE.md).

**AGPL v3**  
Intended for academic, research, and nonprofit institutional use. As long as all derivative works are also open-sourced under the same license, you are free to use, modify, and distribute the software.

**Commercial License**
Intended for commercial use, including production deployments and proprietary applications. This license allows for closed-source derivative works and commercial distribution. Please contact us for more information.