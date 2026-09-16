import os
import requests
from celery import shared_task
from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
result_backend = os.environ.get("REDIS_URL", "redis://localhost:6379")

print("\n" + "="*30)
print(f"DEBUG BROKER URL: {broker_url}")
print(f"DEBUG BACKEND URL: {result_backend}")
print("="*30 + "\n")

celery_app = Celery("tasks", broker=broker_url, backend=result_backend)

@shared_task
def process_audio_task(audio_url: str, task_id: int):
    """
    Downloads audio from the given URL and sends it to the Hugging Face
    Inference API for transcription, completely bypassing local memory limits.
    """
    try:
        # 1. Download the audio file from the frontend URL
        custom_headers = {"User-Agent": "CourierQA/1.0 (Testing)"}
        audio_response = requests.get(audio_url, headers=custom_headers)
        
        if audio_response.status_code != 200:
            return {"status": "error", "message": "Failed to fetch audio from URL."}
        

        # 2. Send the binary audio data to Hugging Face
        hf_api_key = os.environ.get("HF_API_KEY")
        if not hf_api_key:
            return {"status": "error", "message": "HF_API_KEY environment variable is missing."}

        # Using OpenAI's Whisper-Small model hosted for free on Hugging Face
        API_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"
        headers = {"Authorization": f"Bearer {hf_api_key}"}

        hf_response = requests.post(API_URL, headers=headers, data=audio_response.content)

        if hf_response.status_code != 200:
            return {"status": "error", "message": f"Hugging Face API Error: {hf_response.text}"}

        # 3. Extract and return the transcribed text
        result = hf_response.json()
        return {
            "status": "success", 
            "transcription": result.get("text", "No transcription generated.")
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
