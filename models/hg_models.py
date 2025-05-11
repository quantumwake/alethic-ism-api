from typing import Optional

from pydantic import BaseModel

class ImportHgDatasetRequest(BaseModel):
    path: str
    subset: str | None = None
    split: str = "train"
    revision: str | None = None
    vaultKeyId: str | None = None