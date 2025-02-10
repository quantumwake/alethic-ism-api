# Alethic Instruction-Based State Machine (API)

**Contact Us:** Feel free to reach out for more information, comments, questions, or to report bugs and experiments.

**Welcome to the API Layer of Alethic ISM!** While this README is currently brief, more detailed information is on its way. Stay tuned for updates!

**About This Project:** 
The Alethic ISM API layer operates atop various processors with diverse functionalities. We currently support two instruction processors – Anthropic and OpenAI – and are actively working on integrating more, including self-hosted models like Llama2 and Falcon.

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

