from core.base_model import ProcessorStatusCode
from pydantic import BaseModel


class WorkflowEdgeDelete(BaseModel):
    source_node_id: str
    target_node_id: str


class ProcessorStatusUpdated(BaseModel):
    processor_id: str
    status: ProcessorStatusCode
    success: bool
