from typing import Optional

from ismcore.model.base_model import ProcessorStatusCode
from pydantic import BaseModel


class WorkflowEdgeDelete(BaseModel):
    source_node_id: str
    target_node_id: str


class ProcessorStatusUpdated(BaseModel):
    processor_id: str
    status: ProcessorStatusCode
    success: bool

class UserProfileCreateRequest(BaseModel):
    email: str
    name: str
    credentials: str

class BasicResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None