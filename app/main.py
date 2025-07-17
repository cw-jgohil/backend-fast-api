from fastapi import FastAPI
from app.core.config import settings
from app.api import user_router

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI backend!"}

app.include_router(user_router) 