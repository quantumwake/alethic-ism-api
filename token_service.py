import os
import jwt
import datetime

# Replace with a secure key
SECRET_KEY = os.environ.get("SECRET_KEY", "adc7fa1c92a522ff04f465c5d941114cce870f989ac87f0687e6899596be61da")


def generate_jwt(user_id: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # JWT expiration (24 hours)

    payload = {
        'user_id': user_id,
        'exp': expiration
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token