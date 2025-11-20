from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from flask import Flask


def create_flask_adapter(fastapi_app: FastAPI, flask_app: Flask, mount_path: str = "/flask"):
    """
    Mounts a legacy Flask application within the FastAPI application.
    """
    fastapi_app.mount(mount_path, WSGIMiddleware(flask_app))
