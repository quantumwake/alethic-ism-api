import os
import time

from api.dataset import dataset_router
from api.filter import filter_router
from message_router import message_router
from api.processor_state_route import processor_state_router
from api.monitor import monitor_router
from api.processor import processor_router
from api.provider import provider_router
from api.session import session_router
from api.state import state_router
from api.template import template_router
from api.usage import usage_router
from api.user import user_router
from api.project import project_router
from api.validate import validate_router
from api.workflow import workflow_router
from api.state_subscriber import state_channel_router

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from environment import API_ROOT_PATH
from utils.exceptions import CustomException, custom_exception_handler

# set the timezone
tz = os.environ.get("TZ", "UTC")
os.environ["TZ"] = tz
time.tzset()

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
    expose_headers=["Authorization"],  # Make sure Authorization header is exposed
)

# Register the custom exception handler
app.add_exception_handler(CustomException, custom_exception_handler)

app.include_router(user_router, prefix="/user", tags=["users"])
app.include_router(usage_router, prefix="/usage", tags=["usage"])
app.include_router(project_router, prefix="/project", tags=["projects"])
app.include_router(workflow_router, prefix="/workflow", tags=["workflows"])
app.include_router(processor_router, prefix="/processor", tags=["processors"])
app.include_router(processor_state_router, prefix="/processor/state/route", tags=["routes"])
app.include_router(state_router, prefix="/state", tags=["state"])
app.include_router(session_router, prefix="/session", tags=["sessions"])
app.include_router(provider_router, prefix="/provider", tags=["providers"])
app.include_router(filter_router, prefix="/filter", tags=["filters"])
app.include_router(template_router, prefix="/template", tags=["templates"])
app.include_router(monitor_router, prefix="/monitor", tags=["monitors"])
app.include_router(state_channel_router, prefix="/streams", tags=["streams"])
app.include_router(dataset_router, prefix="/dataset", tags=["datasets"])
app.include_router(validate_router, prefix="/validate", tags=["validate"])


@app.on_event("startup")
async def startup_event():
    pass
    # connect_routes = [
    #     "processor/state/router",
    #     "processor/state/sync",
    #     "processor/monitor"
    # ]

    # [await message_router.connect(url) for url in connect_routes]


@app.on_event("shutdown")
async def shutdown_event():
    await message_router.disconnect()
