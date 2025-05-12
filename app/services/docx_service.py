import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
from fpdf import FPDF
from docx import Document
from flask import current_app
import requests


from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from app.config import PDF_DIR
from app.services.drive_service import upload_file_to_drive
import logging


def generate_docx(user_name, ai_response, file_name=None):
    """Génère un fichier Word (DOCX) à partir de la réponse de l'IA"""
    file_path = os.path.join(f"{user_name}_recommendation.docx")
    
    doc = Document()
    
    # Ajouter un titre
    title = doc.add_paragraph(f"Recommandation pour {user_name}")
    title.style = 'Heading1'
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    # Traiter chaque paragraphe de la réponse
    for paragraph in ai_response.split("\n"):
        if paragraph.strip() == "":
            continue  # Ignorer les paragraphes vides
            
        # Vérifier le formatage en gras
        bold_parts = re.split(r"(\*\*.*?\*\*)", paragraph)
        
        p = doc.add_paragraph()
        for part in bold_parts:
            if part.startswith("**") and part.endswith("**"):
                # Texte en gras
                run = p.add_run(part.strip("**"))
                run.bold = True
            else:
                # Texte normal
                p.add_run(part)


    try:
        doc.save(file_path)
        logging.info(f"DOCX file saved  at : {file_path}")

        url=f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/media"

        headers = {
            "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
            # requests library sets Content-Type for multipart/form-data automatically
        }

        files = {
            'file': (file_name, open(file_path, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'), 
            # Correct MIME type for .docx
        }
        data = {
            "messaging_product": "whatsapp"
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status() # Raise an exception for bad status codes
        
        response_json = response.json()
        media_id = response_json.get('id')

        if media_id:
            logging.info(f"File uploaded to WhatsApp, media ID: {media_id}")
             # Optionally: Upload to Google Drive as well
            # upload_file_to_drive(file_path) 
            return media_id
        else:
            logging.error(f"Failed to get media ID from WhatsApp upload response: {response_json}")
            return None
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error uploading file to WhatsApp: {e}")
        logging.error(f"Response status: {e.response.status_code if e.response else 'N/A'}")
        logging.error(f"Response body: {e.response.text if e.response else 'N/A'}")
        return None
    except Exception as e:
        logging.error(f"Error generating or uploading DOCX: {e}")
        return None
    finally:
        # Clean up the local file after upload
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Local file removed: {file_path}")
            except OSError as e:
                logging.error(f"Error removing local file {file_path}: {e}")
    
    # Enregistrer le document

