from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from psycopg import connect, sql
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.db.seeds.run_all_seeds import main as run_all_seeds


ROOT_DIR = Path(__file__).resolve().parents[2]


def ensure_postgres_database() -> None:
    settings = get_settings()
    url = make_url(settings.database_url)
    if not url.drivername.startswith("postgresql"):
        return

    target_db = url.database
    if not target_db:
        raise RuntimeError("DATABASE_URL must include a database name.")

    admin_url = url.set(database="postgres")
    conninfo = admin_url.render_as_string(hide_password=False).replace("+psycopg", "")
    with connect(conninfo, autocommit=True) as conn:
        exists = conn.execute("select 1 from pg_database where datname = %s", (target_db,)).fetchone()
        if exists:
            print(f"Database already exists: {target_db}")
            return
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
        print(f"Created database: {target_db}")


def run_migrations() -> None:
    alembic_config = Config(str(ROOT_DIR / "alembic.ini"))
    command.upgrade(alembic_config, "head")
    print("Alembic upgrade complete.")


def main() -> None:
    ensure_postgres_database()
    run_migrations()
    run_all_seeds()
    print("Bootstrap complete: migrations applied and seed data loaded.")


if __name__ == "__main__":
    main()
