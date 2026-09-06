import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routes.auth import router as auth_router
from app.routes.files import router as files_router
from app.routes.folders import router as folders_router
from app.routes import activities
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routes.shares import router as shares_router
from starlette.middleware.sessions import SessionMiddleware
app = FastAPI(
    title="Cloud Based Media File Storage Service",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET_KEY",
        "dev-session-secret-change-in-production",
    ),
    same_site="lax",
    https_only=False,
)
limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)
app.include_router(auth_router)
app.include_router(files_router)
app.include_router(folders_router)
app.include_router(shares_router)
app.include_router(activities.router)
@app.get("/")
def root():
    return {
        "message": "Cloud Media Storage API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    value = result.scalar()

    return {
        "database": "connected",
        "test": value
    }