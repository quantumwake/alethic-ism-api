# Alethic Instruction-Based State Machine (API)

The Alethic ISM API is the primary entry point for the Alethic ISM UI and the rest of the Alethic ISM platform. 

Here we provide a RESTful API built using FastAPI and provides a simple interface for interacting  with the Alethic ISM
platform.

**Key Points:**
- **Processors**: These are engines that transform an input 'State' into an output 'State'.
- **Current Focus**: Our primary processors are for language processing – Anthropic and OpenAI – with more in development.
- **Configurations**: Each processor uses a State, typically configured through StateConfigLM.
- **StateConfig**: Includes basic settings like name, version, and storage engine.
- **StateConfigLM**: Handles user_templates, system_templates, model names, and provider names.
- **Data Handling**: Processors manage a dataset of key-value pairs, forming a tabular dataset, with each pair processed according to the implemented Processor's functionality.

**Getting Started:**
- **Prerequisites**: Python (versions >=10 and <=11), Conda (preferably miniconda).
- **Repositories to Clone**:
  - `git clone https://github.com/quantumwake/alethic-ism-core.git`
  - `git clone https://github.com/quantumwake/alethic-ism-db.git`
- **Build the Environment**: Run `./build.sh`.
- **Installation**: Create the environment using `conda env create -f environment.yaml`.
- **Updating Models**: Execute `conda install -c ~/miniconda3/envs/local_channel alethic-ism-core alethic-ism-db`.

**Docker Build:**
- Use `./docker_build.sh -t krasaee/alethic-ism-api:local` to build a Docker image

** Required Packages (not available in conda)
- conda env create -f environment.yaml
- conda activate alethic-ism-api
- pip install firebase-admin

