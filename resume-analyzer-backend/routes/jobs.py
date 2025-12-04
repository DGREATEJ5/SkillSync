from fastapi import APIRouter
import json
import os

router = APIRouter(prefix="/jobs", tags=["Jobs"])

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs.json")

@router.get("/")
def get_all_jobs():
    """Return all job descriptions from jobs.json"""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        return {"jobs": jobs}
    except FileNotFoundError:
        return {"jobs": [], "message": "jobs.json not found"}
