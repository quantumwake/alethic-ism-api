from typing import Optional, List

import firebase_admin
from core.base_model import UserProject, UserProfile
from core.processor_state_storage import ProcessorProvider
from core.utils import general_utils
from fastapi import APIRouter, Response, Depends
from firebase_admin import auth, credentials

import token_service
from environment import storage, FIREBASE_CREDENTIALS_JSON_FILE
from http_exceptions import check_null_response

user_router = APIRouter()

# TODO maybe move the user apis into a separate API,
#  seems a bit heavy especially given that the firebase
#  api does not have a conda package

firebase_credential = credentials.Certificate(FIREBASE_CREDENTIALS_JSON_FILE)
default_app = firebase_admin.initialize_app(credential=firebase_credential)


@user_router.post("")
async def create_user_profile(user_details: dict, response: Response) -> Optional[UserProfile]:
    # logging.info('entered into create_user_profile')

    # Fetch the token and create the appropriate user_id uuid
    id_token = user_details['token']
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token['uid']

    # Generate a user_id based on the Firebase UID
    user_id = general_utils.calculate_uuid_based_from_string_with_sha256_seed(uid)

    # Create the user profile in the database
    user_profile = UserProfile(user_id=user_id)
    storage.insert_user_profile(user_profile=user_profile)

    # Generate a JWT for your application
    jwt_token = token_service.generate_jwt(user_id)

    # Set the JWT in the response header
    response.headers['Authorization'] = f"Bearer {jwt_token}"

    print(f"JWT token: {jwt_token}")
    return user_profile


@user_router.get("/{user_id}/projects")
@check_null_response
async def fetch_user_projects(user_id: str = Depends(token_service.verify_jwt)) -> Optional[List[UserProject]]:
    return storage.fetch_user_projects(user_id=user_id)


@user_router.get("")
@check_null_response
async def fetch_user(user_id: str = Depends(token_service.verify_jwt)) -> Optional[UserProfile]:
    return storage.fetch_user_profile(user_id=user_id)


@user_router.get("/{user_id}/provider/processors")
@check_null_response
async def fetch_processor_providers(user_id: str = Depends(token_service.verify_jwt)) \
        -> Optional[List[ProcessorProvider]]:
    return storage.fetch_processor_providers(user_id=user_id)
