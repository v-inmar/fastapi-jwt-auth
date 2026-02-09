#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

python - <<'END'
import time
import sys
import os
from sqlalchemy import create_engine

db_uri = os.environ.get("DATABASE_URL")
if not db_uri:
    print("DATABASE_URL not set")
    sys.exit(1)

# note: psycopg2 is in requirements.txt since alembic uses sync connection to postgresql
db_uri = db_uri.replace("postgresql+asyncpg", "postgresql+psycopg2")

engine = create_engine(db_uri)

while True:
    try:
        with engine.connect():
            # connection was made, do nothing
            # pass is given to let python do its context cleanup before we break the loop
            pass
        break
    except Exception:
        time.sleep(1)
END


echo "PostgreSQL is up, running migrations..."

alembic upgrade head

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4
