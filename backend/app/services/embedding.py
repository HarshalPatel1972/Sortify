from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from typing import List, Dict, Any
import numpy as np

# Load model globally to keep it in memory (runs on CPU)
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

def compute_embeddings(texts: List[str]) -> np.ndarray:
    """
    Computes embeddings for a list of texts.
    """
    if not texts:
        return np.array([])
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings

def cluster_questions(questions: List[Dict[str, Any]], distance_threshold: float = 1.0) -> Dict[int, List[int]]:
    """
    Clusters questions using AgglomerativeClustering.
    Expects questions to have an 'embedding' key (np.ndarray).
    Returns a dictionary of cluster_id -> list of question indices.
    """
    if not questions:
        return {}
        
    embeddings = np.array([q["embedding"] for q in questions])
    
    # We use cosine distance. Scikit-learn agglomerative supports 'cosine' metric.
    # Note: 'cosine' distance = 1 - cosine_similarity.
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        metric='cosine',
        linkage='average',
        distance_threshold=distance_threshold
    )
    
    clustering_model.fit(embeddings)
    
    clusters = {}
    for idx, label in enumerate(clustering_model.labels_):
        label = int(label)
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(idx)
        
    return clusters
