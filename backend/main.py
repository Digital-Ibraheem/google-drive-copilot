# backend/main.py
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from drive_ingest import SCOPES, get_drive_service, list_docs
from retriever import get_top_chunks
from ask_engine import ask_claude

app = FastAPI()

# In-memory token storage (for demo purposes)
_credentials = None

# In-memory document chunks storage (for demo purposes)
# Each chunk follows the format {"text": "...", "source": "..."}
_document_chunks = []

# Model for the ask endpoint request
class QuestionRequest(BaseModel):
    question: str

# OAuth configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8000/oauth/callback"]
    }
}

@app.get("/")
def read_root():
    # Debug route to check if environment variables are loaded
    client_id = os.getenv("GOOGLE_CLIENT_ID", "Not found")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "Not found")
    return {
        "status": "OK",
        "client_id_status": "Available" if client_id != "Not found" else "Missing",
        "client_secret_status": "Available" if client_secret != "Not found" else "Missing"
    }

@app.get("/oauth/start")
def start_oauth():
    """Initiates OAuth flow by redirecting to Google OAuth."""
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )
    flow.redirect_uri = CLIENT_CONFIG["web"]["redirect_uris"][0]
    
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    return RedirectResponse(authorization_url)

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """Handles OAuth callback, exchanges code for token, and lists docs."""
    global _credentials
    
    # Get the authorization code from the request
    code = request.query_params.get("code")
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )
    flow.redirect_uri = CLIENT_CONFIG["web"]["redirect_uris"][0]
    
    # Exchange authorization code for credentials
    flow.fetch_token(code=code)
    _credentials = flow.credentials
    
    # Use the credentials to list Google Docs
    docs = list_docs()
    
    # Format the response
    result = []
    for doc in docs:
        result.append({
            "id": doc["id"],
            "title": doc["name"],
            "type": doc["mimeType"]
        })
    
    return {"documents": result}

# Override the authenticate function from drive_ingest to use our stored credentials
def get_credentials():
    return _credentials

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Endpoint to ask questions about the ingested documents
    """
    global _document_chunks
    
    # Ensure we have chunks to search through
    if not _document_chunks:
        try:
            # Try to load chunks from a file if not in memory
            _document_chunks = load_chunks_from_file()
        except:
            raise HTTPException(
                status_code=400,
                detail="No document chunks available. Please ingest documents first."
            )
    
    # Get the relevant chunks based on the question
    relevant_chunks = get_top_chunks(request.question, _document_chunks)
    if not relevant_chunks:
        return {"answer": "No relevant information found.", "sources": []}
    
    # Extract just the chunks from the (chunk, score) tuples
    chunks_only = [chunk for chunk, _ in relevant_chunks]
    
    # Get answer from Claude
    answer, sources = ask_claude(request.question, chunks_only)
    
    return {"answer": answer, "sources": sources}

@app.post("/ingest")
async def ingest_documents():
    """
    Process and ingest documents from Google Drive
    """
    global _document_chunks
    
    # This would normally call functions to:
    # 1. Get documents from Drive
    # 2. Extract text
    # 3. Chunk the text
    # 4. Store the chunks
    
    # For now, return placeholder message
    # In a real implementation, we would process documents here
    return {"status": "Not yet implemented. Use /documents to see available docs."}

def save_chunks_to_file(chunks):
    """Save document chunks to a JSON file"""
    with open("document_chunks.json", "w") as f:
        json.dump(chunks, f)

def load_chunks_from_file():
    """Load document chunks from a JSON file"""
    try:
        with open("document_chunks.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
