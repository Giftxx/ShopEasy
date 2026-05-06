from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(tempfile.gettempdir()) / "shopeasy_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from app.db.base import Base
from app.db.models import *  # noqa: F401,F403
from app.db.session import SessionLocal, engine
from app.db.seeds.run_workflow_01_seed import seed_workflow_01
from app.db.seeds.run_workflow_02_seed import seed_workflow_02
from app.db.seeds.run_workflow_03_seed import seed_workflow_03
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_workflow_01(db)
        seed_workflow_02(db)
        seed_workflow_03(db)
        db.commit()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
