import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Enum, ForeignKey, 
    Text, LargeBinary, Boolean, JSON
)
from sqlalchemy.orm import relationship
from .database import Base

class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    error = "error"

class TopicSource(str, enum.Enum):
    keyword_rule = "keyword_rule"
    cluster_llm = "cluster_llm"
    manual_override = "manual_override"

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(JobStatus), default=JobStatus.queued)
    total_pdfs = Column(Integer, default=0)
    processed_pdfs = Column(Integer, default=0)

    pdfs = relationship("SourcePDF", back_populates="job", cascade="all, delete-orphan")
    clusters = relationship("Cluster", back_populates="job", cascade="all, delete-orphan")

class SourcePDF(Base):
    __tablename__ = "source_pdfs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    status = Column(Enum(JobStatus), default=JobStatus.queued)

    job = relationship("Job", back_populates="pdfs")
    questions = relationship("Question", back_populates="source_pdf", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    source_pdf_id = Column(Integer, ForeignKey("source_pdfs.id"), nullable=False)
    page_start = Column(Integer, nullable=False)
    page_end = Column(Integer, nullable=False)
    bbox_json = Column(JSON, nullable=False) # coords per page
    extracted_text = Column(Text, nullable=False)
    text_hash = Column(String, nullable=False, index=True) # sha256 normalized
    embedding = Column(LargeBinary, nullable=True) # float32 array blob
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    topic = Column(String, nullable=True)
    topic_source = Column(Enum(TopicSource), nullable=True)
    duplicate_of_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    crop_image_path = Column(String, nullable=True)

    source_pdf = relationship("SourcePDF", back_populates="questions")
    cluster = relationship("Cluster", back_populates="questions")
    # self-referential relationship for duplicates
    duplicates = relationship("Question", backref="canonical_question", remote_side=[id])

class Cluster(Base):
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    representative_question_ids = Column(JSON, nullable=False) # list of ints
    topic_label = Column(String, nullable=True)
    confidence = Column(String, nullable=True) # e.g. "high", "low" or float string

    job = relationship("Job", back_populates="clusters")
    questions = relationship("Question", back_populates="cluster")

class TopicLabelCache(Base):
    __tablename__ = "topic_label_cache"
    text_hash = Column(String, primary_key=True, index=True) # pk, normalized question text hash
    topic = Column(String, nullable=False)

class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens_est = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    purpose = Column(String, nullable=False)
    cache_hit = Column(Boolean, default=False)
