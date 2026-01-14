import logging
import src.config

logging.basicConfig(level=logging.getLevelName(src.config.settings.LOG_LEVEL))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router.user import router as user_router


tags_metadata = [
    {
        "name": "users",
        "description": "Get information about users",
    },
]

app = FastAPI(debug=src.config.settings.DEBUG, openapi_tags=tags_metadata)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user_router)


@app.get("/", status_code=200)
def healthcheck():
    return {"message": "health ok"}
