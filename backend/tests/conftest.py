import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-0123456789")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.dependencies.database import get_db
from app.main import app
from app.models import User
from app.repositories import user_repository as users
from app.services.auth_service import seed_roles

PASSWORD = "Password123"


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    seed_roles(session)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db, email, role="student", active=True):
    user = User(
        full_name=email.split("@")[0].title(),
        email=email,
        hashed_password=hash_password(PASSWORD),
        role_id=users.get_role_by_name(db, role).id,
        is_active=active,
    )
    db.add(user)
    db.commit()
    return user


def auth_headers(client, email):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def staff(db):
    """One user per role: hod, admin(department_admin), lab, faculty, student."""
    for email, role in [
        ("hod@x.com", "hod"), ("admin@x.com", "department_admin"),
        ("lab@x.com", "lab_staff"), ("fac@x.com", "faculty"), ("stud@x.com", "student"),
    ]:
        make_user(db, email, role)
