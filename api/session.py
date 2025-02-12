from typing import List

from core.base_model import SessionMessage, Session
from fastapi import APIRouter, Depends

from api import token_service
from environment import storage
from utils.http_exceptions import check_null_response

session_router = APIRouter()


@session_router.post("/create")
@check_null_response
async def create_session(user_id=Depends(token_service.verify_jwt)) -> Session:
    return storage.create_session(user_id=user_id)


@session_router.delete('/{session_id}')
@check_null_response
async def delete_session(session_id: str) -> int:
    raise NotImplementedError()


@session_router.get('/{session_id}/messages')
@check_null_response
async def fetch_session_messages(session_id: str, user_id=Depends(token_service.verify_jwt)) -> List[SessionMessage]:
    return storage.fetch_session_messages(user_id=user_id, session_id=session_id)
