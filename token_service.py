import os
import jwt
import datetime

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

# Replace with a secure key
SECRET_KEY = os.environ.get("SECRET_KEY", "adc7fa1c92a522ff04f465c5d941114cce870f989ac87f0687e6899596be61da")

# Create an HTTPBearer instance
security = HTTPBearer()


def generate_jwt(user_id: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # JWT expiration (24 hours)

    payload = {
        'user_id': user_id,
        'exp': expiration
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Extract and decode the JWT
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # Optionally, you can check additional claims in the payload
        # For example, checking if the token has expired or if the user has the correct roles
        # return "77c17315-3013-5bb8-8c42-32c28618101f"     // TODO NOTE: login bypass
        return payload['user_id']  # Return theƒj payload for further use in your route
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
