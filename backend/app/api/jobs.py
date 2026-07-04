from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Job, SourcePDF, Cluster, Question
from ..config import settings
import shutil
import os

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("")
def create_job(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    # Create a new job
    job = Job(total_pdfs=len(files))
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Ensure upload dir exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save files and create SourcePDF entries
    for file in files:
        file_path = os.path.join(settings.UPLOAD_DIR, f"{job.id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        pdf_entry = SourcePDF(
            job_id=job.id,
            filename=file.filename,
            storage_path=file_path
        )
        db.add(pdf_entry)
    
    db.commit()
    
    # Trigger worker task synchronously in background
    from ..worker import run_job_pipeline
    background_tasks.add_task(run_job_pipeline, job.id)
    
    return {"job_id": job.id, "message": "Job created and queued"}

@router.get("/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "total_pdfs": job.total_pdfs,
        "processed_pdfs": job.processed_pdfs
    }

@router.get("/{job_id}/clusters")
def get_job_clusters(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()
    result = []
    for c in clusters:
        qs = db.query(Question).filter(Question.cluster_id == c.id).all()
        result.append({
            "id": c.id,
            "topic_label": c.topic_label,
            "questions": [{"id": q.id, "extracted_text": q.extracted_text, "crop_image_path": q.crop_image_path} for q in qs]
        })
    return result

@router.patch("/{job_id}/clusters/{cluster_id}")
def update_cluster(job_id: int, cluster_id: int, topic_label: str, db: Session = Depends(get_db)):
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id, Cluster.job_id == job_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
        
    cluster.topic_label = topic_label
    # Also update questions
    for q in cluster.questions:
        q.topic = topic_label
        q.topic_source = "manual_override"
    db.commit()
    return {"message": "Updated"}

@router.patch("/{job_id}/questions/{question_id}")
def update_question_topic(job_id: int, question_id: int, new_topic: str, db: Session = Depends(get_db)):
    question = db.query(Question).join(SourcePDF).filter(Question.id == question_id, SourcePDF.job_id == job_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    question.topic = new_topic
    question.topic_source = "manual_override"
    question.cluster_id = None # detached from cluster
    db.commit()
    return {"message": "Updated"}

from ..services.pdf_generator import generate_topic_pdf
import zipfile

@router.post("/{job_id}/finalize")
def finalize_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    questions = db.query(Question).join(SourcePDF).filter(SourcePDF.job_id == job_id, Question.duplicate_of_question_id.is_(None)).all()
    
    # Group by topic
    topics_map = {}
    for q in questions:
        topic = q.topic or "Uncategorized"
        if topic not in topics_map:
            topics_map[topic] = []
        topics_map[topic].append(q)
        
    job_output_dir = os.path.join(settings.OUTPUT_DIR, f"job_{job_id}")
    os.makedirs(job_output_dir, exist_ok=True)
    
    pdf_paths = []
    for topic, qs in topics_map.items():
        # sort by source pdf and page
        qs.sort(key=lambda x: (x.source_pdf.filename, x.page_start))
        q_dicts = [{"source_pdf_id": x.source_pdf_id, "page_start": x.page_start, "crop_image_path": x.crop_image_path} for x in qs]
        
        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])
        out_pdf = os.path.join(job_output_dir, f"{safe_topic}.pdf")
        generate_topic_pdf(topic, q_dicts, out_pdf)
        pdf_paths.append(out_pdf)
        
    # Zip them
    zip_path = os.path.join(settings.OUTPUT_DIR, f"job_{job_id}_output.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for p in pdf_paths:
            zipf.write(p, os.path.basename(p))
            
    return {"message": "Finalized"}

from fastapi.responses import FileResponse

@router.get("/{job_id}/download")
def download_job(job_id: int):
    zip_path = os.path.join(settings.OUTPUT_DIR, f"job_{job_id}_output.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Output not found or not finalized")
    return FileResponse(zip_path, filename=f"question_bank_{job_id}.zip")

from ..models import LLMCallLog

@router.get("/{job_id}/llm-usage")
def get_llm_usage(job_id: int, db: Session = Depends(get_db)):
    logs = db.query(LLMCallLog).all() # Just getting all for simplicity, could scope by job
    usage = {"gemini": 0, "groq": 0}
    for log in logs:
        if log.provider in usage:
            usage[log.provider] += 1
    return {"usage": usage}
