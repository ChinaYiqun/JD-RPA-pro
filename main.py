import os
import shutil
import sys



current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from service.OCR import is_ocr_task, process_ocr_request
from my_tools.utils import clear
from fastapi import FastAPI
from service.all_task import *
from service.plan import *
from app_logging import setup_logger


app = FastAPI()
logging = setup_logger("main")
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fastapi-health-check"}

@app.get("/api/lam/taskConfig")
def get_task_config():
    result = get_config()
    logging.info(result)
    return result

@app.post("/api/lam/planAction")
async def plan_action(request: PlanActionRequest):
    result = None
    if is_ocr_task(request):
        result = process_ocr_request(request)
    else:
        result = process_request(request)
    logging.info(result)
    return result.dict()


if __name__ == '__main__':
    #uvicorn main:app --host 0.0.0.0 --port 6666 --reload
    mg = MongoDBClient()
    mg.clear_all_history()
    task_dir = os.path.join(current_dir, "task")
    clear(task_dir)
    task_dir = os.path.join(current_dir, "img_mark_log")
    clear(task_dir)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6666)
