import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.extract_service import ResumeExtractor
from services.vectorstore_service import VectorStoreService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_PATH = os.path.join(BASE_DIR, "data", "jobs.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load job data
with open(JOBS_PATH, "r", encoding="utf-8") as f:
    JOBS = json.load(f)

# FastAPI app
app = FastAPI(title="Job Matching RAG System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
extractor = ResumeExtractor()
vectorstore = VectorStoreService()

# Build vectorstore index on startup
docs = [
    {
        "content": job["description"] + " " + " ".join(job["skills"]),
        **job
    }
    for job in JOBS
]
vectorstore.build_index(docs)

# Allowed MIME types
ALLOWED_TYPES = [
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain"
]


@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )

    # Save file
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # Extract text
    resume_text = extractor.extract_from_file(file)
    resume_lower = resume_text.lower()

    # Query vectorstore
    top_matches = vectorstore.query(resume_text, k=3)

    results = []
    for match in top_matches:
        job_skills = match.get("skills", [])
        matched_skills = [s for s in job_skills if s.lower() in resume_lower]

        results.append({
            "id": match.get("id"),
            "title": match.get("title"),
            "description": match.get("description"),
            "skills": job_skills,
            "matched_skills": matched_skills,
            "semantic_score": match.get("semantic_score"),
            "keyword_score": match.get("keyword_score"),
            "final_score": match.get("final_score"),
        })

    return {
        "matches": results,
        "saved_file": save_path,
        "content_type": file.content_type
    }


@app.get("/")
async def root():
    return {"message": "Job Matching RAG API is running."}
