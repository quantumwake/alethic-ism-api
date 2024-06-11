from typing import Optional, List

import firebase_admin
from core.base_model import UserProject, UserProfile
from core.processor_state_storage import ProcessorProvider
from core.utils import general_utils
from fastapi import APIRouter
from firebase_admin import auth, credentials

from environment import storage
from http_exceptions import check_null_response

user_router = APIRouter()

# TODO maybe move the user apis into a separate API,
#  seems a bit heavy especiailly given that the firebase
#  api does not have a conda package

firebase_credential_path = "/Users/kasrarasaee/quantum-ism-firebase-adminsdk-vnxbq-699289861f.json"
firebase_credential = credentials.Certificate(firebase_credential_path)
default_app = firebase_admin.initialize_app(credential=firebase_credential)

@user_router.post("/")
@check_null_response
async def create_user_profile(user_details: dict) -> Optional[UserProfile]:
    # fetch the token and create the appropriate user_id uuid
    id_token = user_details['token']
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token['uid']  # use the uid from firebase to create the sha256 hash exchanged for a uuid
    user_id = general_utils.calculate_uuid_based_from_string_with_sha256_seed(uid)

    # create the user profile in the database
    user_profile = UserProfile(user_id=user_id)
    storage.insert_user_profile(user_profile=user_profile)
    return user_profile


@user_router.get("/{user_id}/projects")
@check_null_response
async def fetch_user_projects(user_id: str) -> Optional[List[UserProject]]:
    return storage.fetch_user_projects(user_id=user_id)


@user_router.get("/{user_id}/provider/processors")
@check_null_response
async def fetch_processor_providers(user_id: str) \
        -> Optional[List[ProcessorProvider]]:
    return storage.fetch_processor_providers(user_id=user_id)
