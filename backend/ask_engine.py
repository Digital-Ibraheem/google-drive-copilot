import os
import requests
import json
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def ask_claude(question: str, chunks: List[Dict], max_chunks: int = 3) -> Tuple[str, List[str]]:
    """
    Process a user question using Claude API with relevant document chunks as context.
    
    Args:
        question (str): The user's question
        chunks (List[Dict]): List of relevant chunks, each with "text" and "source" keys
        max_chunks (int): Maximum number of chunks to include in the prompt
    
    Returns:
        Tuple[str, List[str]]: (Claude's answer, list of unique sources used)
    """
    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
    # Limit to top chunks
    chunks = chunks[:max_chunks]
    
    # Extract unique sources
    sources = list(set(chunk["source"] for chunk in chunks))
    
    # Build the context from chunks
    context = "\n\n---\n\n".join([
        f"Document: {chunk['source']}\n\n{chunk['text']}"
        for chunk in chunks
    ])
    
    # Construct the system prompt
    system_prompt = (
        "You are a helpful AI assistant that answers questions based on the provided documents. "
        "If the answer can be found in the documents, cite the document source names in your answer. "
        "If the answer cannot be found in the documents, say so clearly and suggest what additional "
        "information might be needed."
    )
    
    # Construct the user message
    user_message = f"Here are some relevant documents:\n\n{context}\n\n---\n\nQuestion: {question}"
    
    # API endpoint
    url = "https://api.anthropic.com/v1/messages"
    
    # Request headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    # Request body
    data = {
        "model": "claude-3-7-sonnet-latest",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "system": system_prompt
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse the response
        result = response.json()
        answer = result["content"][0]["text"]
        
        return answer, sources
    
    except Exception as e:
        # Return error message and empty sources list
        error_msg = f"Error querying Claude API: {str(e)}"
        return error_msg, []

# Example usage:
# question = "What is the infrastructure plan?"
# top_chunks = [{"text": "...", "source": "document1.txt"}, ...]
# answer, sources = ask_claude(question, top_chunks)
