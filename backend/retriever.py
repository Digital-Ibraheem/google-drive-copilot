import numpy as np
from typing import List, Dict, Tuple, Union
import re
from collections import Counter

# Try to import sentence-transformers, but provide fallback if not available
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

def get_top_chunks(question: str, chunks: List[Dict], top_k: int = 3) -> List[Tuple[Dict, float]]:
    """
    Find the top k most relevant chunks for a given question.
    
    Args:
        question (str): User's question
        chunks (List[Dict]): List of chunk dictionaries with format {"text": text, "source": source}
        top_k (int): Number of top chunks to return
        
    Returns:
        List[Tuple[Dict, float]]: List of tuples containing (chunk_dict, similarity_score)
    """
    if not chunks:
        return []
    
    # Limit to top_k or available chunks, whichever is smaller
    top_k = min(top_k, len(chunks))
    
    if SEMANTIC_SEARCH_AVAILABLE:
        return semantic_search(question, chunks, top_k)
    else:
        return keyword_search(question, chunks, top_k)

def semantic_search(question: str, chunks: List[Dict], top_k: int) -> List[Tuple[Dict, float]]:
    """
    Find the top k most relevant chunks using sentence embeddings and cosine similarity.
    
    Args:
        question (str): User's question
        chunks (List[Dict]): List of chunk dictionaries
        top_k (int): Number of top chunks to return
        
    Returns:
        List[Tuple[Dict, float]]: List of tuples containing (chunk_dict, similarity_score)
    """
    # Load pre-trained model (faster, lighter model suitable for CPU)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create embeddings
    question_embedding = model.encode([question], convert_to_tensor=True)
    chunk_texts = [chunk["text"] for chunk in chunks]
    chunk_embeddings = model.encode(chunk_texts, convert_to_tensor=True)
    
    # Calculate similarities
    similarities = cosine_similarity(
        question_embedding.cpu().numpy(), 
        chunk_embeddings.cpu().numpy()
    )[0]
    
    # Get indices of top_k highest similarities
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    # Return top chunks with their scores
    return [(chunks[i], float(similarities[i])) for i in top_indices]

def keyword_search(question: str, chunks: List[Dict], top_k: int) -> List[Tuple[Dict, float]]:
    """
    Find the top k most relevant chunks using simple keyword overlap.
    Used as fallback when sentence-transformers is not available.
    
    Args:
        question (str): User's question
        chunks (List[Dict]): List of chunk dictionaries
        top_k (int): Number of top chunks to return
        
    Returns:
        List[Tuple[Dict, float]]: List of tuples containing (chunk_dict, similarity_score)
    """
    # Extract keywords from question (lowercase, remove punctuation, split)
    question_words = re.sub(r'[^\w\s]', '', question.lower()).split()
    question_words = [w for w in question_words if len(w) > 2]  # Filter out short words
    
    # Count question words frequency
    question_counter = Counter(question_words)
    
    scores = []
    for chunk in chunks:
        # Process chunk text the same way
        chunk_text = chunk["text"].lower()
        chunk_words = re.sub(r'[^\w\s]', '', chunk_text).split()
        chunk_words = [w for w in chunk_words if len(w) > 2]
        
        # Count matches
        matches = sum(question_counter.get(word, 0) for word in chunk_words)
        
        # Score is number of matches divided by chunk length (to normalize)
        # Add a small value to avoid division by zero
        score = matches / (len(chunk_words) + 0.1)
        scores.append(score)
    
    # Get indices of top_k highest scores
    top_indices = np.argsort(scores)[-top_k:][::-1]
    
    # Return top chunks with their scores
    return [(chunks[i], float(scores[i])) for i in top_indices]
