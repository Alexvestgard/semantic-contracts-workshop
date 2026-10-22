"""Initialize only the dedicated museum_eval database from the existing seed."""

import importlib.util
import os
import sys
from pathlib import Path

import psycopg
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect


def main():
    dsn = os.environ["EVAL_ADMIN_DSN"]
    if psycopg.conninfo.conninfo_to_dict(dsn).get("dbname") != "museum_eval":
        raise ValueError("The eval loader only accepts the dedicated museum_eval database.")
    assets = Path(os.environ.get("EVAL_ASSETS", "/seed"))
    revision = assets / "db_migrations/versions/00e9b3375a5f_create_met_museum_seed_tables.py"
    spec = importlib.util.spec_from_file_location("museum_revision", revision)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine(dsn.replace("postgresql://", "postgresql+psycopg://", 1))
    with engine.begin() as conn:
        if not inspect(conn).has_table("object"):
            with Operations.context(MigrationContext.configure(conn)):
                module.upgrade()
    sys.path.insert(0, str(assets))
    import seed_db
    seed_db.DB_CONFIG = dsn
    seed_db.load_and_insert_data(str(assets / "db_migrations/raw_data/objects.json"))
    with psycopg.connect(dsn) as conn:
        conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        conn.execute("REVOKE TEMPORARY ON DATABASE museum_eval FROM PUBLIC")
        if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='eval_reader'").fetchone():
            conn.execute("CREATE ROLE eval_reader LOGIN PASSWORD 'eval_reader' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT")
        conn.execute("ALTER ROLE eval_reader SET default_transaction_read_only = on")
        conn.execute("ALTER ROLE eval_reader SET statement_timeout = '2s'")
        conn.execute("GRANT CONNECT ON DATABASE museum_eval TO eval_reader")
        conn.execute("GRANT USAGE ON SCHEMA public TO eval_reader")
        conn.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO eval_reader")
    print("Dedicated evaluation database seeded; eval_reader has SELECT access.")


if __name__ == "__main__":
    main()
