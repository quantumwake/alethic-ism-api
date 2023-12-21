# Alethic Instruction-Based State Machine (API)

First feel free to contact us if you need more information or have a comment, question, bug, experiment, ...

Welcome to the README, tons of information here. Of course, we are well aware that there is barely any, but we are working on it. Stay tuned! 

Essentially this project is a layer ontop of the underlying processors, which can vary from functionality. Currently there are two available instruction processors, for anthropic and openai, we are working on including other models, including self hosted models such as llama2, falcon, etc.

There are really a few things you need to know.
a. A processor is a kind of engine that takes in an input of type State and outputs another instance of type State.
b. Currently there are two main processors for language processing, Anthropic and OpenAI, of course we are working on more, including self-hosted models (top priority)
c. Each processor takes in a State, which includes a configuration, usually a StateConfigLM.
d. StateConfig instances take a basic configuration, such as name, version, state storage engine. 
e. In the case of StateConfigLM, these configuration types take in user_templates, system_templates, model name, and model provider name.
f. A processor is responsible for taking a State input, which contains a dataset of key, value pairs, making up a tabular dataset.
g. Each pair is submitted for processing to the implementation of the Processor. The implemented processor is responsible for taking the input performing some function on it, such as calling a GPT API, reading the response from it, building a new output State dataset, forwarding the previous states information (configurable via query inheritance columns)
h. TBD

Please take a look at the alethic-ism-processor-openai as an example.

Stay tuned for more information.

# Prerequisites
- python (>9 <12)
- conda (miniconda)
- conda install conda-build


Repositories: 
- git clone https://github.com/quantumwake/alethic-ism-core.git
- git clone https://github.com/quantumwake/alethic-ism-db.git

After having cloned the repo, execute:
- ./build.sh


# Installation
You should just be able to create the environment
- conda env create -f environment.yaml

When you need to update the core and db models
- conda install -c ~/miniconda3/envs/local_channel alethic-ism-core alethic-ism-db

# Dependencies (when available remotely - currently not)
- conda install alethic-ism-core alethic-ism-db


# Build Docker
I must admit, the script name is less than acceptable. 
- ./docker_build_conda_package.sh

this should produce a docker image, hopefully.

