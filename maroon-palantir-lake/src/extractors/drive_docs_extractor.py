import os
import logging
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Scopes for read-only access to Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveDocsExtractor:
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self._authenticate()

    def _authenticate(self):
        """Authenticates the user locally to get Drive API access."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    logging.warning(f"OAuth credentials not found at {self.credentials_path}. Skipping Drive extraction.")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

    def extract_all(self) -> List[Dict[str, Any]]:
        documents = []
        if not self.creds:
            logging.error("No valid credentials. Cannot extract from Google Drive.")
            return documents

        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Query for documents, AI Studio files, etc.
            results = service.files().list(
                pageSize=100, fields="nextPageToken, files(id, name, mimeType)").execute()
            items = results.get('files', [])

            if not items:
                logging.info("No files found in Google Drive.")
            else:
                logging.info(f"Found {len(items)} files in Google Drive.")
                for item in items:
                    mime_type = item['mimeType']
                    # Attempt to extract text from Google Docs
                    if mime_type == 'application/vnd.google-apps.document':
                        try:
                            request = service.files().export_media(fileId=item['id'], mimeType='text/plain')
                            content = request.execute().decode('utf-8')
                            documents.append({
                                "source_type": "google_drive",
                                "source_uri": f"gdrive://{item['id']}",
                                "content": content,
                                "metadata": {
                                    "name": item['name'],
                                    "mime_type": mime_type
                                }
                            })
                            logging.info(f"Extracted Google Doc: {item['name']}")
                        except Exception as e:
                            logging.warning(f"Failed to export doc {item['name']}: {e}")
                    else:
                        logging.info(f"Skipping non-doc file: {item['name']} ({mime_type})")
        except Exception as e:
            logging.error(f"Error communicating with Google Drive API: {e}")

        logging.info(f"Extracted {len(documents)} text documents from Google Drive.")
        return documents

if __name__ == "__main__":
    extractor = DriveDocsExtractor()
    docs = extractor.extract_all()
    print(f"Sample extraction: Found {len(docs)} text files.")
