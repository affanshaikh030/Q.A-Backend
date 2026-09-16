import os
import requests
from celery import shared_task, Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
result_backend = os.environ.get("REDIS_URL", "redis://localhost:6379")

celery_app = Celery("tasks", broker=broker_url, backend=result_backend)

@shared_task
def process_audio_task(audio_url: str, task_id: int):
    """
    Downloads audio from the given URL and sends it to the Hugging Face
    Inference API for transcription, completely bypassing local memory limits.
    """
    try:
        # 1. Download the audio file from the frontend URL with User-Agent bypass
        custom_headers = {"User-Agent": "CourierQA/1.0 (Testing)"}
        audio_response = requests.get(audio_url, headers=custom_headers)
        
        if audio_response.status_code != 200:
            from app.core.database import SessionLocal 
            from app.models.task import AnalysisTask
            db = SessionLocal()
            try:
                db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                if db_task:
                    db_task.status = "ERROR"
                    db.commit()
            finally:
                db.close()
            return {"status": "error", "message": "Failed to fetch audio from URL."}
        
        # 2. Send the binary audio data to Hugging Face
        hf_api_key = os.environ.get("HF_API_KEY")
        if not hf_api_key:
            from app.core.database import SessionLocal 
            from app.models.task import AnalysisTask
            db = SessionLocal()
            try:
                db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                if db_task:
                    db_task.status = "ERROR"
                    db.commit()
            finally:
                db.close()
            return {"status": "error", "message": "HF_API_KEY environment variable is missing."}

        API_URL = "https://router.huggingface.co/models/openai/whisper-small"
        headers = {"Authorization": f"Bearer {hf_api_key}"}
        
        hf_response = requests.post(API_URL, headers=headers, data=audio_response.content)
        
        if hf_response.status_code != 200:
            from app.core.database import SessionLocal 
            from app.models.task import AnalysisTask 
            db = SessionLocal()
            try:
                db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
                if db_task:
                    db_task.status = "ERROR"
                    db.commit()
            finally:
                db.close()
            return {"status": "error", "message": f"Hugging Face API Error: {hf_response.text}"}
        
        result = hf_response.json()
        transcription_text = result.get("text", "No transcription generated.")
        
        # 3. UPDATE THE DATABASE (Success - breaks the PENDING loop)
        from app.core.database import SessionLocal 
        from app.models.task import AnalysisTask 

        db = SessionLocal()
        try:
            db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if db_task:
                db_task.status = "SUCCESS"
                db_task.transcription = transcription_text
                db.commit()
        finally:
            db.close()
            
        return {"status": "success", "message": "Database updated."}

    except Exception as e:
        from app.core.database import SessionLocal 
        from app.models.task import AnalysisTask 
        
        db = SessionLocal()
        try:
            db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if db_task:
                db_task.status = "ERROR"
                db.commit()
        finally:
            db.close()
            
        return {"status": "error", "message": str(e)}
