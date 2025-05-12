import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
from fpdf import FPDF
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from app.config import PDF_DIR
from app.services.drive_service import upload_file_to_drive


def generate_docx(user_name, ai_response):
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
    
    # Enregistrer le document
    doc.save(file_path)
    upload_file_to_drive(file_path)
    return file_path
