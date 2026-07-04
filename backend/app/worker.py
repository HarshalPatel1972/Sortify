import os
import json
from sqlalchemy.orm import Session
from .config import settings
from .models import Job, SourcePDF, Question, JobStatus, Cluster
from .services.pdf_splitter import process_pdf
from .services.dedup import deduplicate_questions
from .services.embedding import compute_embeddings, cluster_questions
from .services.llm_provider import label_cluster
from .database import SessionLocal

# In-memory pipeline replacing RQ
def run_job_pipeline(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
            
        # 1. Process all PDFs
        for pdf_entry in job.pdfs:
            _process_source_pdf(pdf_entry.id, db)
            
        # 2. Dedup & Cluster
        _dedup_and_cluster_job(job.id, db)
        
        # 3. Label
        _label_job_clusters(job.id, db)
        
    except Exception as e:
        print(f"Error in pipeline for job {job_id}: {e}")
    finally:
        db.close()

def _process_source_pdf(pdf_id: int, db: Session):
    try:
        pdf_entry = db.query(SourcePDF).filter(SourcePDF.id == pdf_id).first()
        if not pdf_entry:
            return
            
        pdf_entry.status = JobStatus.processing
        db.commit()
        
        # 1. Split
        questions_data = process_pdf(pdf_entry.storage_path, settings.OUTPUT_DIR, pdf_id)
        
        # Insert raw questions
        for qd in questions_data:
            q = Question(
                source_pdf_id=qd["source_pdf_id"],
                page_start=qd["page_start"],
                page_end=qd["page_end"],
                bbox_json=qd["bbox_json"],
                extracted_text=qd["extracted_text"],
                text_hash="", # will be populated in dedup
                crop_image_path=qd["crop_image_path"]
            )
            db.add(q)
        db.commit()
        
        pdf_entry.status = JobStatus.done
        job = pdf_entry.job
        job.processed_pdfs += 1
        db.commit()
            
    except Exception as e:
        pdf_entry.status = JobStatus.error
        db.commit()
        print(f"Error processing PDF {pdf_id}: {e}")

def _dedup_and_cluster_job(job_id: int, db: Session):
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.processing
        db.commit()
        
        # Fetch all questions for this job
        questions = db.query(Question).join(SourcePDF).filter(SourcePDF.job_id == job_id).all()
        q_dicts = [{"id": q.id, "extracted_text": q.extracted_text} for q in questions]
        
        # 2. Dedup
        q_dicts = deduplicate_questions(q_dicts)
        
        # Update db with hashes and duplicate links
        unique_q_dicts = []
        for i, qd in enumerate(q_dicts):
            q = questions[i]
            q.text_hash = qd["text_hash"]
            if qd.get("duplicate_of_index") is not None:
                dup_idx = qd["duplicate_of_index"]
                q.duplicate_of_question_id = q_dicts[dup_idx]["id"]
            else:
                unique_q_dicts.append(qd)
        db.commit()
        
        # 3. Embeddings
        texts = [q["extracted_text"] for q in unique_q_dicts]
        embeddings = compute_embeddings(texts)
        for i, emb in enumerate(embeddings):
            unique_q_dicts[i]["embedding"] = emb
            
            # also update DB
            q_id = unique_q_dicts[i]["id"]
            q = next(q for q in questions if q.id == q_id)
            q.embedding = emb.tobytes()
            
        # 4. Clustering
        clusters = cluster_questions(unique_q_dicts)
        
        # Save clusters
        for label, q_indices in clusters.items():
            rep_ids = [unique_q_dicts[idx]["id"] for idx in q_indices] # all ids for now
            
            cluster_entry = Cluster(
                job_id=job.id,
                representative_question_ids=rep_ids[:5], # Store top 5 for LLM
                topic_label=None # To be filled by LLM
            )
            db.add(cluster_entry)
            db.flush()
            
            # Link questions to cluster
            for idx in q_indices:
                q_id = unique_q_dicts[idx]["id"]
                q = next(q for q in questions if q.id == q_id)
                q.cluster_id = cluster_entry.id
                
                # Link duplicates as well
                duplicates = db.query(Question).filter(Question.duplicate_of_question_id == q.id).all()
                for dup_q in duplicates:
                    dup_q.cluster_id = cluster_entry.id
                    
        db.commit()
        
    except Exception as e:
        job.status = JobStatus.error
        db.commit()
        print(f"Error in dedup_and_cluster for job {job_id}: {e}")

def _label_job_clusters(job_id: int, db: Session):
    try:
        clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()
        for cluster in clusters:
            if cluster.topic_label:
                continue
                
            # Fetch representative questions
            rep_ids = cluster.representative_question_ids
            qs = db.query(Question).filter(Question.id.in_(rep_ids)).all()
            texts = [q.extracted_text for q in qs]
            
            label = label_cluster(texts, db)
            if label:
                cluster.topic_label = label
                
                # Apply to all questions
                for q in cluster.questions:
                    q.topic = label
                    q.topic_source = "cluster_llm"
        
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.done
        db.commit()
        
    except Exception as e:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.error
        db.commit()
        print(f"Error labeling clusters for job {job_id}: {e}")
