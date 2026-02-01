"""
Google Drive storage for Luna journal database.
Uses OAuth 2.0 and Drive API to store one SQLite file per user in their Drive.
"""

import os
import io
import tempfile
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Scopes: only access files created by this app
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
# App data folder name in Drive (user-visible as "Luna Journal")
APP_FOLDER_NAME = "Luna Journal"
DB_FILENAME = "luna_journal.db"


def get_flow(redirect_uri):
    """Build OAuth2 flow with redirect URI (must match Google Cloud Console)."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    return flow


def get_auth_url(redirect_uri):
    """Return the URL to send the user to for Google sign-in."""
    flow = get_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_credentials(code, redirect_uri):
    """Exchange authorization code for credentials. Returns Credentials object."""
    flow = get_flow(redirect_uri)
    flow.fetch_token(code=code)
    creds = flow.credentials
    return creds


def _get_drive_service(creds):
    return build("drive", "v3", credentials=creds)


def _find_or_create_app_folder(service):
    """Find or create the app folder in user's Drive. Returns folder ID."""
    # List files in Drive root, look for folder named APP_FOLDER_NAME
    results = (
        service.files()
        .list(
            q="mimeType='application/vnd.google-apps.folder' and name='"
            + APP_FOLDER_NAME
            + "' and trashed=false",
            spaces="drive",
            fields="files(id, name)",
        )
        .execute()
    )
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    # Create folder
    file_metadata = {
        "name": APP_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]


def _find_db_file_in_folder(service, folder_id):
    """Return file ID of luna_journal.db in folder, or None."""
    results = (
        service.files()
        .list(
            q=f"'{folder_id}' in parents and name='{DB_FILENAME}' and trashed=false",
            spaces="drive",
            fields="files(id, name)",
        )
        .execute()
    )
    files = results.get("files", [])
    return files[0]["id"] if files else None


def get_or_create_db_file(creds):
    """
    Ensure the user's Drive has a luna_journal.db file (create empty if not).
    Returns (local_path, upload_callback).
    - local_path: path to a temp file that can be used as SQLite DB.
    - upload_callback: call this after any DB write to sync back to Drive.
    """
    service = _get_drive_service(creds)
    folder_id = _find_or_create_app_folder(service)
    file_id = _find_db_file_in_folder(service, folder_id)

    fd, local_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    local_path = Path(local_path)

    if file_id:
        # Download existing DB to temp file
        request = service.files().get_media(fileId=file_id)
        with open(local_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
    else:
        # Create empty file; we'll upload after first write (init_database will create tables)
        local_path.touch()

    def upload_to_drive():
        """Upload current local DB back to Drive."""
        if not local_path.exists():
            return
        file_id = _find_db_file_in_folder(service, folder_id)
        media = MediaFileUpload(str(local_path), mimetype="application/x-sqlite3", resumable=True)
        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {"name": DB_FILENAME, "parents": [folder_id]}
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    return local_path, upload_to_drive


def get_user_email(creds):
    """Get the user's email from the token info (optional; for display)."""
    if hasattr(creds, "id_token") and creds.id_token:
        import base64
        import json
        try:
            payload = creds.id_token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload))
            return data.get("email") or data.get("sub", "Signed in with Google")
        except Exception:
            pass
    return "Signed in with Google"
