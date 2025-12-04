"""Small utility to inspect the dev database schema from Python.

Usage (from backend directory):

    python inspect_db.py

This will print:
  - the configured INKQ_PG_URL
  - list of tables in the public schema
  - whether the `users` table is accessible
"""

from sqlalchemy import create_engine, text

from app.config import settings


def main() -> None:
    print("INKQ_PG_URL =", settings.inkq_pg_url)

    engine = create_engine(settings.inkq_pg_url)

    with engine.connect() as conn:
        # List public tables
        rows = conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        ).fetchall()
        tables = [r[0] for r in rows]
        print("Public tables:", tables)

        # Check users table specifically
        try:
            conn.execute(text("SELECT 1 FROM users LIMIT 1"))
            print("Users table: OK (query succeeded)")
        except Exception as exc:
            print("Users table error:", repr(exc))

        # Check sessions table and show a sample session if present
        if "sessions" in tables:
            rows = conn.execute(
                text("SELECT id, user_id, expires_at FROM sessions ORDER BY created_at DESC LIMIT 3")
            ).fetchall()
            print("Recent sessions:", rows)
        else:
            print("Sessions table not found.")


if __name__ == "__main__":
    main()



