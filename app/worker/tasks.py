import os
import time
import requests
from celery import Celery, shared_task
from transformers import pipeline
from app.core.database import SessionLocal
from app.models.task import AnalysisTask

# Initialize Celery
celery_app = Celery("tasks", broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"))
celery_app.conf.task_always_eager = True  # Forces tasks to run locally if needed

@shared_task
def process_audio_task(audio_url: str, task_id: int):
    print(f"Starting analysis for task {task_id} with audio URL: {audio_url}")
    db = SessionLocal()
    try:
        db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if db_task:
            db_task.status = "PROCESSING"
            db.commit()

        # Simulate transcription and processing
        time.sleep(2)
        mock_transcript = "Hello, I am outside your location with your package but the gate is locked."

        if db_task:
            db_task.status = "COMPLETED"
            db_task.result = mock_transcript
            db.commit()
    except Exception as e:
        db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if db_task:
            db_task.status = "ERROR"
            db.commit()
        raise e
    finally:
        db.close()
    
    return {"status": "success", "transcript": mock_transcript}