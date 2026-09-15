import time
from celery import Celery
from transformers import pipeline
from app.core.database import SessionLocal
from app.models.task import AnalysisTask

# Initialize Celery (Using a local dummy broker for Windows testing)
celery_app = Celery("tasks", broker="memory://", backend="cache+memory://")
celery_app.conf.task_always_eager = True # Forces tasks to run locally

# Load the real machine learning model
print("Loading AI model... this might take a moment.")
sentiment_analyzer = pipeline("sentiment-analysis")
print("AI model loaded successfully!")

@celery_app.task(bind=True)
def process_audio_task(self, audio_url: str, task_id: int):
    # 1. Simulate the transcription of a delivery call
    time.sleep(2) 
    mock_transcript = "Hello, I am outside your location with your package but the gate is locked."
    
    # 2. Run real AI sentiment analysis on the text
    ai_result = sentiment_analyzer(mock_transcript)[0]
    sentiment_label = ai_result['label'] 
    
    # 3. Map it to our new logistics business logic
    dispute_risk = "High" if sentiment_label == "NEGATIVE" else "Low"
    
    insights = {
        "sentiment": sentiment_label,
        "fcr_status": dispute_risk
    }
    
    # 4. Connect to the database and save the real AI results
    db = SessionLocal()
    try:
        db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if db_task:
            db_task.transcript = mock_transcript
            db_task.insights = insights
            db_task.status = "COMPLETED"
            db.commit()
    finally:
        db.close()
        
    print(f"Task {task_id} completed with real AI insights: {insights}")