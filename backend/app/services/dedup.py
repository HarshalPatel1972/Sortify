import hashlib
import re
from typing import List, Dict, Any, Tuple
from rapidfuzz import fuzz
from datasketch import MinHash, MinHashLSH

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def get_minhash(text: str, num_perm: int = 128) -> MinHash:
    m = MinHash(num_perm=num_perm)
    for word in text.split():
        m.update(word.encode('utf-8'))
    return m

def deduplicate_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identifies duplicates and marks them.
    Modifies the dictionaries in place by setting 'duplicate_of_index' if it's a duplicate.
    Returns the updated list.
    """
    seen_hashes = {}
    lsh = MinHashLSH(threshold=0.85, num_perm=128)
    
    for i, q in enumerate(questions):
        norm_text = normalize_text(q["extracted_text"])
        exact_hash = compute_hash(norm_text)
        
        q["text_hash"] = exact_hash
        q["duplicate_of_index"] = None
        
        # 1. Exact match
        if exact_hash in seen_hashes:
            q["duplicate_of_index"] = seen_hashes[exact_hash]
            continue
            
        seen_hashes[exact_hash] = i
        
        # 2. Near match
        mhash = get_minhash(norm_text)
        candidates = lsh.query(mhash)
        
        is_dup = False
        for cand_idx in candidates:
            cand_q = questions[cand_idx]
            cand_text = normalize_text(cand_q["extracted_text"])
            
            # Verify with RapidFuzz
            score = fuzz.token_sort_ratio(norm_text, cand_text)
            if score >= 92:
                # Mark as duplicate
                q["duplicate_of_index"] = cand_idx
                is_dup = True
                break
                
        if not is_dup:
            lsh.insert(f"q_{i}", mhash)
            
    return questions
