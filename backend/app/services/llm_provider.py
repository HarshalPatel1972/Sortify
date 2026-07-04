import time
import json
import logging
from typing import List, Tuple, Optional
import google.generativeai as genai
from openai import OpenAI
from ..config import settings
from sqlalchemy.orm import Session
from ..models import LLMCallLog

logger = logging.getLogger(__name__)

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Configure Groq via OpenAI client
groq_client = None
if settings.GROQ_API_KEY:
    groq_client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )

def _log_call(db: Session, provider: str, model: str, tokens: int, purpose: str, cache_hit: bool):
    if db:
        log_entry = LLMCallLog(
            provider=provider,
            model=model,
            prompt_tokens_est=tokens,
            purpose=purpose,
            cache_hit=cache_hit
        )
        db.add(log_entry)
        db.commit()

def label_cluster(questions: List[str], db: Session = None) -> Optional[str]:
    """
    Calls LLM to label a cluster of questions.
    Returns the topic label.
    """
    prompt = "Given these sample questions, respond with ONLY the single most specific topic name, nothing else.\n\n"
    for i, q in enumerate(questions):
        prompt += f"Q{i+1}: {q}\n"
        
    est_tokens = len(prompt) // 4
    
    # Try Gemini first
    if settings.GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            label = response.text.strip()
            _log_call(db, "gemini", "gemini-1.5-flash", est_tokens, "label_cluster", False)
            return label
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
            
    # Fallback to Groq
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies questions into a single specific topic name."},
                    {"role": "user", "content": prompt}
                ]
            )
            label = response.choices[0].message.content.strip()
            _log_call(db, "groq", "llama3-8b-8192", est_tokens, "label_cluster", False)
            return label
        except Exception as e:
            logger.warning(f"Groq failed: {e}")
            
    return None
