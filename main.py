from monitor import monitor_router
from processor import processor_router
from processor_state import processor_state_router
from provider import provider_router
from route import route_router
from state import state_router
from template import template_router
from user import user_router
from project import project_router
from workflow import workflow_router
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from environment import API_ROOT_PATH
from exceptions import CustomException, custom_exception_handler

title = "Instruction State Machine API"
summary = """This is the interface between the backend and user interface, it allows for 
creation of workflows, processors, states and execution of processor state associations."""

if API_ROOT_PATH:
    app = FastAPI(
        title=title,
        summary=summary,
        root_path=API_ROOT_PATH
    )
else:
    app = FastAPI(
        title=title,
        summary=summary
    )

origins = [
    "http://localhost",
    "https://localhost",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    "https://127.0.0.1:3000",
    "https://127.0.0.1",
    "https://localhost:3000",
    "http://localhost:3000",
    "https://ism.quantumwake.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the custom exception handler
app.add_exception_handler(CustomException, custom_exception_handler)

app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(project_router, prefix="/project", tags=["project"])
app.include_router(workflow_router, prefix="/workflow", tags=["workflow"])
app.include_router(processor_router, prefix="/processor", tags=["processor"])
app.include_router(processor_state_router, prefix="/processor/state", tags=["processor state"])
app.include_router(state_router, prefix="/state", tags=["state"])
app.include_router(route_router, prefix="/route", tags=["route"])
app.include_router(provider_router, prefix="/provider", tags=["provider"])
app.include_router(template_router, prefix="/template", tags=["template"])
app.include_router(monitor_router, prefix="/monitor", tags=["monitor log event"])
