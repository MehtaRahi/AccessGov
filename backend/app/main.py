import os
import requests

# Strong SSL Bypass for HuggingFace & Requests
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"

requests.packages.urllib3.disable_warnings()
old_request = requests.Session.request
def new_request(*args, **kwargs):
    kwargs['verify'] = False
    return old_request(*args, **kwargs)
requests.Session.request = new_request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router

app = FastAPI(title="AccessGov API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.session import engine
from app.db.models import Base
Base.metadata.create_all(bind=engine)

from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/api/auth")

app.include_router(api_router, prefix="/api")

from apscheduler.schedulers.background import BackgroundScheduler
from app.services.data_pipeline import run_pipeline
import logging

logger = logging.getLogger(__name__)

@app.on_event("startup")
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run the automated pipeline every 7 days (weekly)
    scheduler.add_job(run_pipeline, 'interval', days=7)
    scheduler.start()
    logger.info("APScheduler started: Data pipeline scheduled to run every 7 days.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
