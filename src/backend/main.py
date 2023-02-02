# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#


import logging.config
import os
from os import path
from typing import Union

from auth import routers as auth_routers
from db.database import Base, SessionLocal, engine
from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger

from fastapi.responses import FileResponse
from projects import project_routes
from tasks import tasks_routes
from users import user_routes

# from .auth import login_route


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from fastapi.middleware.cors import CORSMiddleware
from os import path

# setup loggers
log_file_path = path.join(path.dirname(path.abspath("logging.conf")), "logging.conf")

logging.config.fileConfig(
    os.path.join(os.getcwd(), "logging.conf"), disable_existing_loggers=False
)  # main.py runs from code/
logger = logging.getLogger(__name__)

gunicorn_error_logger = logging.getLogger("gunicorn.error")
gunicorn_logger = logging.getLogger("gunicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.handlers = gunicorn_error_logger.handlers

fastapi_logger.handlers = gunicorn_error_logger.handlers

if __name__ != "__main__":
    fastapi_logger.setLevel(gunicorn_logger.level)
else:
    fastapi_logger.setLevel(logging.DEBUG)


Base.metadata.create_all(bind=engine)

api = FastAPI()

api.include_router(user_routes.router)
api.include_router(project_routes.router)
api.include_router(tasks_routes.router)
api.include_router(debug_routes.router)
api.include_router(central_routes.router)

origins = [
    "http://localhost",
    "http://localhost:8080",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api.include_router(auth_routers.router)


@api.get("/")
def read_root():
    logger.info("logging from the root logger")
    return {"Hello": "Big, big World"}


@api.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@api.get("/images/{image_filename}")
def get_images(image_filename: str):
    path = f"./src/backend/images/{image_filename}"
    return FileResponse(path)