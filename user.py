from typing import Optional, List
from db.models import UserProject
from fastapi import APIRouter
from environment import state_storage

user_router = APIRouter()


@user_router.get("/{user_id}/projects")
async def fetch_user_projects(user_id: str) -> Optional[List[UserProject]]:
    return state_storage.fetch_user_projects(user_id=user_id)

