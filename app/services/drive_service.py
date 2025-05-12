import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
# Charger les credentials
CREDENTIALS_FILE = "/app/services/credentials.json"
FOLDER_ID = "1L-CYkX-iHSQwNwIVDpiZzScJg-dkhBDF"


def upload_file_to_drive(file_path,):
    """
    Upload un fichier sur Google Drive dans le dossier spécifié.
    """
    try:
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/drive.file"])
        service = build("drive", "v3", credentials=credentials)

        file_metadata = {
            "name": os.path.basename(file_path),
            "parents": [FOLDER_ID]
        }
        media = MediaFileUpload(file_path)
        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        file_id = file.get("id")
        file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

        print(f"✅ Fichier sauvegardé : {file_url}")
        return file_url
    except Exception as e:
        print(f"❌ Erreur upload Drive : {e}")
        return None
