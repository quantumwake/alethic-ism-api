import os
import sys

import dotenv
import json

from core.processor_state import find_state_files, StateConfigLM
from db.processor_state_db import ProcessorStateDatabaseStorage

dotenv.load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL',
                              'postgresql://postgres:postgres1@localhost:5432/postgres')




states = find_state_files(
    search_path='/Users/kasrarasaee/Development/quantumwake/temp_processor_code/states/animallm/prod',
    search_recursive=True,
    state_path_match='.pickle'
)

abs_path = os.getcwd()
# new_absolute_path = f"{abs_path}/templates"
new_absolute_path = f'/Users/kasrarasaee/Development/quantumwake/temp_processor_code/templates'

# states = {file: state for file, state in states if '0_8' in file }

for state_file, state in states.filter_items():

    # TODO for backwards compatibility issue
    if 'version' not in state.config.__dict__ or not state.config.version:
        state.config.version = "Version 0.0"

    def update_content_path_if_any(template_config_path: str):

        if not template_config_path:
            return None

        # update it to the absolute path
        template_config_path = template_config_path.replace('../templates', new_absolute_path) \
            if template_config_path else None

        if not os.path.exists(template_config_path):
            return None

        with open(template_config_path, 'r') as fio:
            template_config = json.load(fio)

            if 'template_content_file' in template_config:
                content_file = template_config['template_content_file']
                content_file = content_file.replace('../templates', new_absolute_path)
                template_config['template_content_file'] = content_file

        with open(template_config_path, 'w') as fio:
            json.dump(template_config, fio)

        return template_config_path

    if isinstance(state.config, StateConfigLM):
        state.config.user_template_path = update_content_path_if_any(state.config.user_template_path)
        state.config.system_template_path = update_content_path_if_any(state.config.system_template_path)

    for key_definition in state.config.primary_key:
        key_definition.required = False \
            if 'required' not in key_definition.__dict__ \
            else key_definition.required

    for key_definition in state.config.query_state_inheritance:
        key_definition.required = False \
            if 'required' not in key_definition.__dict__ \
            else key_definition.required

    # storage = ProcessorStateDatabaseStorage(database_url=DATABASE_URL)
    # storage.save_state(state)

    state_file_basename = os.path.basename(state_file)
    state_file_basename = state_file_basename.replace('.pickle', '.json')
    output_path = f'./archive_states/{state_file_basename}'
    # state.save_state()
    with open(output_path, 'w') as fio:
        fio.write(state.model_dump_json(indent=4))

