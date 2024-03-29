from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src import config
from src.api.graphql import graphql


def _add_module(parent: FastAPI, module: FastAPI, prefix: str) -> None:
    parent.mount(prefix, module)


def _setup_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def init_app(app: FastAPI) -> None:
    _setup_cors(app)
    _add_module(app, graphql, "")
