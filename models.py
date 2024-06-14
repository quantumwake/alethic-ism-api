from pydantic import BaseModel


class WorkflowEdgeDelete(BaseModel):
    source_node_id: str
    target_node_id: str

