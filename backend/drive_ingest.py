import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying scopes, delete the saved token
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
_credentials = None

def authenticate():
    """Handle Google OAuth using Installed App flow and store token in memory."""
    global _credentials
    
    # First try to get credentials from main.py if available
    try:
        from main import get_credentials
        web_creds = get_credentials()
        if web_creds:
            return web_creds
    except (ImportError, AttributeError):
        pass
    
    # Fall back to installed app flow if no web credentials
    if not _credentials:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        _credentials = flow.run_local_server(port=0)
    return _credentials

def get_drive_service():
    """Create and return Google Drive API service."""
    credentials = authenticate()
    return build('drive', 'v3', credentials=credentials)

def list_docs():
    """List Google Docs in user's Drive."""
    service = get_drive_service()
    response = service.files().list(
        q="mimeType='application/vnd.google-apps.document'",
        spaces='drive',
        fields='files(id, name, mimeType)'
    ).execute()
    
    return response.get('files', [])

def get_doc_content(doc_id):
    """Fetch text content from a Google Doc using export API."""
    service = get_drive_service()
    request = service.files().export_media(fileId=doc_id, mimeType='text/plain')
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    return fh.getvalue().decode('utf-8')

# Simple usage example
if __name__ == "__main__":
    docs = list_docs()
    if docs:
        print(f"Found {len(docs)} docs. First doc: {docs[0]['name']}")
        content = get_doc_content(docs[0]['id'])
        print(f"Content preview: {content[:100]}...")
