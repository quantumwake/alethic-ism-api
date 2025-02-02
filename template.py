from typing import Optional
from core.processor_state import InstructionTemplate
from fastapi import APIRouter
from environment import storage

template_router = APIRouter()


@template_router.get("/{template_id}")
async def fetch_instruction_template(template_id: str) -> Optional[InstructionTemplate]:
    return storage.fetch_template(template_id=template_id)


@template_router.post('/create')
async def merge_instruction_template(template: InstructionTemplate) -> InstructionTemplate:
    storage.insert_template(template=template)
    return template


@template_router.post('/create/text')
async def merge_instruction_template_text(template_id: str,
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


@template_router.put('/{template_id}/rename/{new_name}')
async def rename_template(template_id: str, new_name: str) -> Optional[InstructionTemplate]:
    template = storage.fetch_template(template_id=template_id)
    template.template_path = new_name
    storage.insert_template(template=template)
    return template
