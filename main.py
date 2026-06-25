from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from domain.user import user_router
from process import router as file_router
from db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router.router)
app.include_router(file_router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
