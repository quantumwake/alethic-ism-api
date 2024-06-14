from pydantic import BaseModel
route

class WorkflowEdgeDelete(BaseModel):
    source_node_id: str
    target_node_id: str

