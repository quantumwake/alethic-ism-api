from typing import Optional, List

import firebase_admin
from core.base_model import UserProject, UserProfile
from core.processor_state_storage import ProcessorProvider
from core.utils import general_utils
from fastapi import APIRouter
from firebase_admin import auth, credentials

from environment import storage, FIREBASE_CREDENTIALS_JSON_FILE
from http_exceptions import check_null_response

user_router = APIRouter()

# TODO maybe move the user apis into a separate API,
#  seems a bit heavy especiailly given that the firebase
#  api does not have a conda package

firebase_credential = credentials.Certificate(FIREBASE_CREDENTIALS_JSON_FILE)
default_app = firebase_admin.initialize_app(credential=firebase_credential)

@user_router.post()
# @check_null_response
async def create_user_profile(user_details: dict) -> Optional[UserProfile]:

    print('entered into create_user_profile')
    print(f' using the following data: "{str(user_details)}"')
    # fetch the token and create the appropriate user_id uuid
    id_token = user_details['token']

    print(f'token id: {id_token}')
    decoded_token = auth.verify_id_token(id_token)
    print(f'decoded token: {decoded_token}')

    uid = decoded_token['uid']  # use the uid from firebase to create the sha256 hash exchanged for a uuid
    print(f'decoded uid: {uid}')

    user_id = general_utils.calculate_uuid_based_from_string_with_sha256_seed(uid)
    print(f'user id: {user_id}')

    # create the user profile in the database
    user_profile = UserProfile(user_id=user_id)
    storage.insert_user_profile(user_profile=user_profile)
    print(f'stored user profile: {user_id}')

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
