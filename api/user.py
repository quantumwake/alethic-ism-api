from typing import Optional, List

# TODO re-ennable this and also add in other providers, maybe we should use something different or implement our own
from fastapi import APIRouter, Response, Depends
from ismcore.model.base_model import UserProfile, UserProject, ProcessorProvider, UserProfileCredential
from ismcore.utils import general_utils

from api import token_service
from environment import storage, ENABLED_LOCAL_AUTH, ENABLED_FIREBASE_AUTH
from models.models import UserProfileCreateRequest
from utils.http_exceptions import check_null_response

from firebase_admin import auth

user_router = APIRouter()

# TODO maybe move the user apis into a separate API,
#  seems a bit heavy especially given that the firebase
#  api does not have a conda package

firebase_app = None
def initialize_firebase_app():
    if not ENABLED_FIREBASE_AUTH:
        raise Exception("Firebase authentication is not enabled, set ENABLED_FIREBASE_AUTH=true")
    global firebase_app

    if firebase_app is not None:
        return firebase_app

    """
    Initialize the Firebase app with the credentials JSON file.
    This is used to verify the Firebase ID tokens.
    """
    try:
        import firebase_admin
        from environment import FIREBASE_CREDENTIALS_JSON_FILE
        from firebase_admin import auth, credentials
        firebase_credential = credentials.Certificate(FIREBASE_CREDENTIALS_JSON_FILE)
        firebase_app = firebase_admin.initialize_app(credential=firebase_credential)
        return firebase_app
    except Exception as e:
        print(f"Error initializing Firebase app: {e}")
        return None

@user_router.post("/google")
async def create_user_profile_google(user_details: dict, response: Response) -> Optional[UserProfile]:
    if not ENABLED_FIREBASE_AUTH:
        raise Exception("Firebase authentication is not enabled, set ENABLED_FIREBASE_AUTH=true")

    # Initialize the Firebase app
    initialize_firebase_app()

    # Fetch the token and create the appropriate user_id uuid
    id_token = user_details['token']
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token['uid']

    # Generate a user_id based on the Firebase UID
    user_id = general_utils.calculate_uuid_based_from_string_with_sha256_seed(uid)

    # fetch values from firebase user details
    email = user_details['user']['email']
    name = user_details['user']['displayName']

    # Create the user profile in the database

    # Check if the user profile already exists; if yes, we don't need to create it again
    user_profile = storage.fetch_user_profile(user_id=user_id)
    if not user_profile:
        user_profile = UserProfile(
            user_id=user_id,
            email=email,
            name=name,
            max_agentic_units=10000)
        storage.insert_user_profile(user_profile=user_profile)

    # Generate a JWT for your application
    jwt_token = token_service.generate_jwt(user_id)

    # Set the JWT in the response header
    response.headers['Authorization'] = f"Bearer {jwt_token}"

    # print(f"JWT token: {jwt_token}")
    return user_profile


@user_router.post("/basic")
async def create_user_profile_basic(request: UserProfileCreateRequest, response: Response) -> Optional[UserProfile]:
    if not ENABLED_LOCAL_AUTH:
        raise Exception("local user creation is disabled, set but caution with ENABLED_LOCAL_AUTH=true")

    if not request.email:
        raise Exception("email cannot be empty")

    # TODO check if the password is empty
    if not request.credentials:
        raise Exception("credentials cannot be empty")

    user_id = general_utils.calculate_uuid_based_from_string_with_sha256_seed(request.email)
    user_profile = storage.fetch_user_profile(user_id=user_id)

    # Check if the user profile already exists, if it does we don't need to create it again
    if not user_profile:
        # Create the user profile in the database
        storage.insert_user_profile(user_profile=UserProfile(
            user_id=user_id,
            email=request.email,
            name=request.name,
            max_agentic_units=10000))

    # Check if user profile credential already exists
    user_profile_credential = storage.fetch_user_profile_credential(user_id=user_id)
    if not user_profile_credential:
        # TODO encrypt the password (this is a placeholder)
        encrypted_password = request.credentials

        # insert the credential into the database
        user_profile_credential = storage.insert_user_profile_credential(user_profile_credential=UserProfileCredential(
            user_id=user_id,
            type="encrypted_password",
            credentials=encrypted_password
        ))

    # Check credentials before generating the JWT
    encrypted_password_check = user_profile_credential.credentials
    if request.credentials != encrypted_password_check:
        raise Exception("credentials do not match")

    # Generate a JWT for your application
    jwt_token = token_service.generate_jwt(user_id)

    # Set the JWT in the response header
    response.headers['Authorization'] = f"Bearer {jwt_token}"

    print(f"JWT token: {jwt_token}")
    return user_profile

@user_router.get("/{uid}")
async def fetch_user_profile(uid: str, response: Response) -> Optional[UserProfile]:
    user_id = general_utils.calculate_uuid_based_from_string_with_sha256_seed(uid)
    user_profile = storage.fetch_user_profile(user_id=user_id)
    if user_profile is None:
        response.status_code = 404
        return None
    return user_profile

@user_router.get("/{user_id}/{token_uid}/user")
@check_null_response
async def fetch_user(token_uid: str) -> str:
    # TODO check this over
    return general_utils.calculate_uuid_based_from_string_with_sha256_seed(token_uid)
    # return storage.fetch_user_profile(user_id=user_id)


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
