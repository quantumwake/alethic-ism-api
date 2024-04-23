from typing import Optional
from core.processor_state import InstructionTemplate
from fastapi import APIRouter
from environment import state_storage

template_router = APIRouter()


@template_router.get("/{template_id}")
def fetch_instruction_template(template_id: str) -> Optional[InstructionTemplate]:
    return state_storage.fetch_template(template_id=template_id)


@template_router.post('/create')
def merge_instruction_template(template: InstructionTemplate) -> InstructionTemplate:
    state_storage.insert_template(instruction_template=template)
    return template


@template_router.post('/create/text')
def merge_instruction_template_text(template_id: str,
                                    template_path: str,
                                    template_content: str,
                                    template_type: str,
                                    project_id: str = None):

    # create an instruction template object
    instruction = InstructionTemplate(
        template_id=template_id,
        template_path=template_path,
        template_content=template_content,
        template_type=template_type,
        project_id=project_id
    )

    return merge_instruction_template(instruction)
