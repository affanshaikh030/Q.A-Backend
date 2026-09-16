#!/usr/bin/env bash

# Start Celery in the background, optimized for 512MB RAM
celery -A app.worker.tasks worker --pool=solo --loglevel=info &

# Start FastAPI in the foreground
uvicorn app.main:app --host 0.0.0.0 --port $PORT
