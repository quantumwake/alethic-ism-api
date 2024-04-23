from starlette.middleware.cors import CORSMiddleware
from environment import API_ROOT_PATH, state_storage
from exceptions import CustomException, custom_exception_handler
from fastapi import FastAPI, UploadFile, File

from processor import processor_router
from states import state_router
from user import user_router
from project import project_router
from workflow import workflow_router

if API_ROOT_PATH:
    app = FastAPI(root_path=API_ROOT_PATH)
else:
    app = FastAPI()

origins = [
    "http://localhost",
    "https://localhost",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    "https://127.0.0.1:3000",
    "https://127.0.0.1",
    "https://localhost:3000",
    "http://localhost:3000",
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

routes = {}
message_config = {}

app.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(project_router, prefix="/project", tags=["project"])
app.include_router(workflow_router, prefix="/workflow", tags=["workflow"])
app.include_router(processor_router, prefix="/processor", tags=["processor"])
app.include_router(state_router, prefix="/state", tags=["state"])

# app.include_router(user_router, prefix="/user", tags=["user"])
# app.include_router(product_router, prefix="/products", tags=["products"])
# app.include_router(order_router, prefix="/orders", tags=["orders"])



# @app.get("/processor/model/types", tags=["Processor"])
# def get_processor_model_types() -> Optional[List[Model]]:
#     return state_storage.fetch_models()

#
# @app.post("/processor/execute", tags=["Processor"])
# async def execute(processor_state: ProcessorState) -> ProcessorState:
#
#     # identify the route
#     route = get_route_by_processor(processor_id=processor_state.processor_id)
#
#     # set the process to queued
#     processor_state.status = StatusCode.QUEUED
#     state_storage.update_processor_state(processor_state)
#     message = processor_state.model_dump_json()
#     route.process.send(message)
#
#     return processor_state
