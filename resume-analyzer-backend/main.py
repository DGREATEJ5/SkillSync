import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from services.extract_service import ResumeExtractor
from services.vectorstore_service import VectorStoreService
from services.llm_service import enhance_job_matches
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

# Build vectorstore index ON STARTUP
docs = [
    {
        "content": f"{job['description']} {' '.join(job['skills'])}",
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

    # Save uploaded file
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # Extract text from resume
    resume_text = extractor.extract_from_file(file)
    resume_lower = resume_text.lower()

    # Vectorstore hybrid search
    top_matches = vectorstore.query(resume_text, k=3)

    # GPT-enhanced recommendation
    gpt_recommendation = enhance_job_matches(resume_text, top_matches)

    # Compute matched skills
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
        "recommendation": gpt_recommendation,
        "matches": results,
        "saved_file": save_path,
        "content_type": file.content_type
    }

@app.post("/add_job")
async def add_job(job: dict = Body(...)):
    """
    Add a new job to jobs.json and update vectorstore.
    Required fields: title, description, skills, company, posted_by, employment_type, location, salary_range
    """
    required_fields = [
        "title",
        "description",
        "skills",
        "company",
        "posted_by",
        "employment_type",
        "location",
        "salary_range"
    ]
    for field in required_fields:
        if field not in job:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    # Read current jobs
    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Generate new ID
    new_id = max([j["id"] for j in jobs]) + 1 if jobs else 1
    job["id"] = new_id

    # Append and save
    jobs.append(job)
    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4)

    # Update vectorstore
    vectorstore.add_job({
        "content": f"{job['description']} {' '.join(job['skills'])}",
        **job
    })

    return {"message": "Job added successfully", "job": job}


@app.post("/upload_jobs_json")
async def upload_jobs_json(jobs: list[dict]):
    added_jobs = []
    for job in jobs:
        # Validate required fields
        required_fields = ["title", "description", "skills", "company", "posted_by", "employment_type", "location", "salary_range"]
        for field in required_fields:
            if field not in job:
                raise HTTPException(status_code=400, detail=f"Missing field: {field}")
        
        # Add directly to Pinecone
        vectorstore.add_job({
            "content": f"{job['description']} {' '.join(job['skills'])}",
            **job
        })
        added_jobs.append(job)

    return {"message": f"{len(added_jobs)} jobs uploaded and indexed successfully."}



@app.get("/")
async def root():
    return {"message": "Job Matching RAG API is running."}
