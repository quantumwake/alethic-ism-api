from typing import Optional

from pydantic import BaseModel


class ImportHgDatasetRequest(BaseModel):
    path: str
    subset: str | None = None
    split: str = "train"
    revision: str | None = None
    vaultKeyId: str | None = None


class ExportHgDatasetRequest(BaseModel):
    namespace: str
    dataset_name: str | None = None
    private: bool = True
    commit_message: str | None = None
    revision: str | None = None
    vaultKeyId: str | None = None