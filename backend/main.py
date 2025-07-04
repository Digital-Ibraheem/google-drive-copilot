# backend/main.py
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
import os
from typing import Dict

from drive_ingest import SCOPES, get_drive_service, list_docs

app = FastAPI()

# In-memory token storage (for demo purposes)
_credentials = None

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
    return {"status": "OK"}

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
