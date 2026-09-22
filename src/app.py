import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from core.security import hash_password
from db import create_db_and_tables, engine
from models import User
from routers.auth import router as auth_router
from routers.booking import router as booking_router

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

SEED_USERS = (
    ("admin", "admin1234", True),
    ("user1", "user1234", False),
    ("user2", "user2234", False),
)


def seed_users(session: Session) -> None:
    for username, password, is_admin in SEED_USERS:
        exists = session.exec(select(User).where(User.username == username)).first()
        if exists is None:
            session.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                    is_admin=is_admin,
                )
            )
    session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_users(session)

    logger.info("Application started")
    yield
    logger.info("Application stopped")


app = FastAPI(
    title="Python Developer Assessment BBL",
    version="1.0.0",
    description="Python Developer Assessment BBL",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(booking_router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/static/login.html")


@app.get("/api/health")
def health_check():
    return {"message": "OK"}


@app.get("/api/ready")
def ready_check():
    return {"message": "OK"}
