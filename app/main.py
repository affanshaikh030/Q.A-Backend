from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware # 1. ADD THIS IMPORT
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.models.task import AnalysisTask
from app.worker.tasks import process_audio_task

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Local E-commerce Audio API")

# 2. ADD THIS MIDDLEWARE BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any frontend to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... leave the rest of your app/main.py file exactly the same below this line ...
# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TaskCreateRequest(BaseModel):
    audio_url: str

@app.post("/api/tasks")
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    # 1. Save pending task to database
    db_task = AnalysisTask(audio_url=payload.audio_url, status="PENDING")
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 2. Send to background worker
    process_audio_task.delay(payload.audio_url, db_task.id)
    
    return {"message": "Task queued", "task_id": db_task.id}

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task