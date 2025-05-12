# app/services/drive_service.py

import os
import json # <--- Importer le module json
import logging # <--- Importer logging (recommandé)
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Supprimer ou commenter la ligne suivante :
# CREDENTIALS_FILE = "./app/services/credentials.json"

# Assurez-vous que FOLDER_ID est défini (peut-être aussi via une variable d'env?)
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1L-CYkX-iHSQwNwIVDpiZzScJg-dkhBDF") # Exemple avec fallback

def upload_file_to_drive(file_path):
    """
    Upload un fichier sur Google Drive en utilisant les credentials depuis une variable d'environnement.
    """
    credentials = None
    # Récupérer le contenu JSON depuis la variable d'environnement
    google_creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not google_creds_json_str:
        logging.error("La variable d'environnement GOOGLE_CREDENTIALS_JSON est manquante.")
        return None

    try:
        # Parser la chaîne JSON en dictionnaire Python
        google_creds_dict = json.loads(google_creds_json_str)

        # Créer les credentials à partir du dictionnaire
        credentials = Credentials.from_service_account_info(
            google_creds_dict,
            scopes=["https://www.googleapis.com/auth/drive.file"] # Spécifier les scopes requis
        )
        logging.info("Credentials Google chargés avec succès depuis la variable d'environnement.")

    except json.JSONDecodeError:
        logging.error("Échec du parsing de GOOGLE_CREDENTIALS_JSON. Vérifiez son contenu.")
        return None
    except Exception as e:
        logging.error(f"Erreur lors du chargement des credentials Google depuis l'environnement : {e}")
        return None

    # Vérifier si les credentials ont bien été chargés
    if not credentials:
        return None

    # --- Le reste de votre fonction upload_file_to_drive ---
    try:
        service = build("drive", "v3", credentials=credentials)

        file_metadata = {
            "name": os.path.basename(file_path),
            "parents": [FOLDER_ID]
        }

        # Vérifier si le fichier local existe avant l'upload
        if not os.path.exists(file_path):
             logging.error(f"Fichier non trouvé pour l'upload Drive : {file_path}")
             return None

        media = MediaFileUpload(file_path) # Possiblement ajouter mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document' si nécessaire

        logging.info(f"Upload de {file_path} vers Google Drive (dossier {FOLDER_ID})...")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id" # Demander seulement l'ID
        ).execute()

        file_id = file.get("id")

        if file_id:
            file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            logging.info(f"✅ Fichier sauvegardé sur Drive : {file_url}")
            return file_url
        else:
            logging.error("Upload Drive réussi mais aucun ID de fichier retourné.")
            return None

    except Exception as e:
        # Log plus détaillé si possible (ex: erreurs spécifiques de l'API Google)
        logging.error(f"❌ Erreur upload Drive : {e}")
        # if hasattr(e, 'content'): logging.error(f"Détail erreur API Drive : {e.content}")
        return None