# Alethic Instruction-Based State Machine (API)

The Alethic ISM API is the primary entry point for the Alethic ISM UI and the rest of the Alethic ISM platform. 

**Key Points:**
- **Processors**: These are engines that transform an input 'State' into an output 'State'.
- **Current Focus**: Our primary processors are for language processing – Anthropic and OpenAI – with more in development.
- **Configurations**: Each processor uses a State, typically configured through StateConfigLM.
- **StateConfig**: Includes basic settings like name, version, and storage engine.
- **StateConfigLM**: Handles user_templates, system_templates, model names, and provider names.
- **Data Handling**: Processors manage a dataset of key-value pairs, forming a tabular dataset, with each pair processed according to the implemented Processor's functionality.

**Building from Source**
- **Prerequisites**: Python (versions >=10 and <=11), Conda (preferably miniconda).
- **Repositories to Clone**:
  - `git clone https://github.com/quantumwake/alethic-ism-core.git`

**Docker Build:**
- Use `./docker_build.sh -t krasaee/alethic-ism-api:local` to build a Docker image

** Required Packages (not available in conda)
- `pip install uv`

## License
Alethic ISM is under a DUAL licensing model, please refer to [LICENSE.md](LICENSE.md).

**AGPL v3**  
Intended for academic, research, and nonprofit institutional use. As long as all derivative works are also open-sourced under the same license, you are free to use, modify, and distribute the software.

**Commercial License**
Intended for commercial use, including production deployments and proprietary applications. This license allows for closed-source derivative works and commercial distribution. Please contact us for more information.

