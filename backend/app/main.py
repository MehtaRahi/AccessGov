import os
import requests

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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time

# Database init with retry (postgres may take a moment to be ready)
for attempt in range(5):
    try:
        from app.db.session import engine
        from app.db.models import Base
        Base.metadata.create_all(bind=engine)
        
        # Add missing 'title' column if it doesn't exist (since create_all doesn't alter tables)
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE chats ADD COLUMN title VARCHAR DEFAULT 'New Chat';"))
                conn.commit()
        except Exception:
            pass # Column already exists
            
        break
    except Exception as e:
        if attempt < 4:
            time.sleep(2)
        else:
            print(f"⚠️ Database connection failed after 5 attempts: {e}", flush=True)

from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/api/auth")

from app.api.admin import router as admin_router
app.include_router(admin_router, prefix="/api/admin")

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
