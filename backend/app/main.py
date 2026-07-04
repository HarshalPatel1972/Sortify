from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

app = FastAPI(title="Question Bank Sorter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be specific origins
    allow_credentials=True,
    allow_methods=["*"],
)

from .database import engine, Base
from .models import * # Import models so they register with Base

Base.metadata.create_all(bind=engine)

@app.get("/health")
def health_check():
    return {"status": "ok"}

from .api import api_router
from fastapi.staticfiles import StaticFiles
import os
from .config import settings

app.include_router(api_router, prefix="/api")

os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=settings.OUTPUT_DIR), name="images")
