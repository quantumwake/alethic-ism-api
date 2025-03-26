import traceback
from typing import Dict, List, Any
from fastapi import APIRouter, Body
from ismcore.compiler.secure_runnable import SecurityConfig, SecureRunnableBuilder

validate_router = APIRouter()


@validate_router.post('/python')
async def validate_python_code(
    code_content: str = Body(..., embed=True, media_type="text/plain"),
    queries: List[Dict] = Body(None)
) -> Any:

    config = SecurityConfig(
        max_memory_mb=100,
        max_cpu_time_seconds=5,
        max_requests=50,
        execution_timeout=10,
        enable_resource_limits=False
    )

    try:
        # Create builder and compile the user code
        builder = SecureRunnableBuilder(config)
        runnable = builder.compile(code_content.lstrip())

        # Run the user's code with queries
        results = runnable.process(queries=queries)
        return results

    except SyntaxError as e:
        # Capture syntax errors
        return {
            "error": "Syntax Error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

    except AttributeError as e:
        # Capture attribute-related errors
        return {
            "error": "Attribute Error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

    except TypeError as e:
        # Capture type errors, often from mismatched arguments
        return {
            "error": "Type Error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

    except Exception as e:
        # General exception handler for unexpected errors
        return {
            "error": "Unexpected Error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }