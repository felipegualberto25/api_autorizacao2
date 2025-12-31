from fastapi import FastAPI, UploadFile, File
import os
import uuid

from app.tasks import ocr_task
from celery.result import AsyncResult

app = FastAPI()

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------
# 1) Enviar arquivo
# ---------------------------
@app.post("/ocr")
async def process_file(file: UploadFile = File(...)):

    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as out:
        out.write(await file.read())

    task = ocr_task.delay(filepath)

    return {
        "job_id": task.id,
        "status": "PROCESSING"
    }


# ---------------------------
# 2) Buscar resultado
# ---------------------------
@app.get("/ocr/{job_id}")
async def get_result(job_id: str):

    result = AsyncResult(job_id)

    if not result:
        return {"error": "Job not found"}

    if result.status == "PENDING":
        return {
            "job_id": job_id,
            "status": "PENDING"
        }

    if result.status == "STARTED":
        return {
            "job_id": job_id,
            "status": "PROCESSING"
        }

    if result.status == "FAILURE":
        return {
            "job_id": job_id,
            "status": "ERROR",
            "error": str(result.result)
        }

    # SUCCESS
    data = result.result

    return {
        "job_id": job_id,
        "status": "SUCCESS",
        "codes": data.get("codes"),
        "text": data.get("text")
    }

@app.get("/ocr/log/{job_id}")
def get_log(job_id: str):
    path = f"/app/data/logs/{job_id}.json"

    if not os.path.exists(path):
        raise HTTPException(404, "Log não encontrado")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
