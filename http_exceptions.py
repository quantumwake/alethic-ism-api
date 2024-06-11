from functools import wraps
from fastapi import HTTPException, Request


def check_null_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)
        if response is None:
            raise HTTPException(status_code=404)
        return response
    return wrapper
