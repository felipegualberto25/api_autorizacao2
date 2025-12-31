import os
import uuid
import traceback

from celery import Celery
from fastapi import UploadFile
from app.ocr_engine import ocr_auto
from app.matcher import get_matcher
from app.log_utils import save_debug_log

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

BROKER = os.environ.get("CELERY_BROKER_URL", "redis://ocr_redis:6379/0")
BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://ocr_redis:6379/1")

celery_app = Celery("tasks", broker=BROKER, backend=BACKEND)


@celery_app.task(name="app.tasks.ocr_task")
def ocr_task(filename: str):
    """
    Executa o OCR + Match e gera log explicando decisões.
    """

    job_id = str(uuid.uuid4())

    upload_path = os.path.join(UPLOAD_DIR, filename)

    matcher = get_matcher()

    try:
        # OCR (usando file_path)
        text = ocr_auto(file_path=upload_path)

        # match codes
        codes = matcher.match_codes_from_text(text)

        debug_payload = {
            "filename": filename,
            "job_id": job_id,
            "ocr_text": text,
            "codes": codes,
            "decision_trace": matcher.debug_trace,
        }

        log_path = save_debug_log(job_id, debug_payload)

        return {
            "job_id": job_id,
            "codes": codes,
            "log_path": log_path,
        }

    except Exception as e:
        err = traceback.format_exc()

        debug_payload = {
            "filename": filename,
            "job_id": job_id,
            "error": str(e),
            "traceback": err,
        }

        save_debug_log(job_id, debug_payload)

        return {
            "error": "matcher internal error",
            "details": str(e),
        }
