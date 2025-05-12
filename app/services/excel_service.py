# app/services/excel_service.py

import os
import logging
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.cell import MergedCell
from openpyxl.utils import get_column_letter
# Import your drive service function correctly
try:
    # Adjust the path based on your project structure if necessary
    from .drive_service import upload_file_to_drive
except ImportError:
    from drive_service import upload_file_to_drive # Fallback for different structure/testing

# --- Function 1: Costs (CVU) ---
def generate_costs_excel(user_id, costs_data):
    """
    Génère un fichier Excel pour les coûts variables (CVU), l'upload sur Drive et retourne l'URL.
    Expects costs_data to be a dictionary containing keys like 'costs', 'final_unit_cost', etc.
    """
    excel_path = f"costs_cvu_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None # Ensure wb is defined

    try:
        # Extract data (adjust keys based on how you store it in calcul_cvu.py state)
        costs = costs_data.get('costs_list', []) # Assuming you store the list of costs here
        final_unit_cost = costs_data.get('cvu', 0) # Assuming final CVU is stored here
        # You might need to recalculate transport/labor costs here if not stored directly
        # Or pass them explicitly if they are stored in the state.
        # For simplicity, let's assume they might need recalculation or aren't displayed
        # Add placeholder values or adjust logic as needed.
        total_mp = sum(c.get('total_unit_cost', 0) for c in costs)
        transport_cost_display = total_mp * 0.01 # Example recalculation
        labor_cost_display = total_mp * 0.30  # Example recalculation


        wb = Workbook()
        ws = wb.active
        ws.title = "Coûts Variables"

        ws['A1'] = "Calcul du coût variable unitaire"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:E1')
        ws['A1'].alignment = Alignment(horizontal='center')

        headers = ["Elements du CV", "Unité", "Quantité", "Prix unitaire $", "Montant total $"]
        header_row = 3
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        row_num = header_row + 1
        for cost in costs:
            ws.cell(row=row_num, column=1, value=cost.get('name', 'N/A'))
            ws.cell(row=row_num, column=2, value=cost.get('unit', 'N/A')).alignment = Alignment(horizontal='center')
            ws.cell(row=row_num, column=3, value=f"{cost.get('quantity_per_unit', 0):.5f}").alignment = Alignment(horizontal='center')
            ws.cell(row=row_num, column=4, value=f"{cost.get('cost_per_unit', 0):.3f}").alignment = Alignment(horizontal='center')
            ws.cell(row=row_num, column=5, value=f"{cost.get('total_unit_cost', 0):.3f}").alignment = Alignment(horizontal='center')
            row_num += 1

        # Ajout des totaux (ajusté)
        ws.cell(row=row_num, column=1, value="Total MP").font = Font(bold=True)
        ws.cell(row=row_num, column=5, value=f"{total_mp:.3f}").alignment = Alignment(horizontal='center')
        row_num += 1

        ws.cell(row=row_num, column=1, value="Transport (Ex: 1%)").font = Font(bold=True)
        ws.cell(row=row_num, column=5, value=f"{transport_cost_display:.3f}").alignment = Alignment(horizontal='center')
        row_num += 1

        ws.cell(row=row_num, column=1, value="Main d'oeuvre (Ex: 30%)").font = Font(bold=True)
        ws.cell(row=row_num, column=5, value=f"{labor_cost_display:.3f}").alignment = Alignment(horizontal='center')
        row_num += 1

        ws.cell(row=row_num, column=1, value="Coût variable unitaire").font = Font(bold=True)
        ws.cell(row=row_num, column=5, value=f"{final_unit_cost:.3f}").alignment = Alignment(horizontal='center')


        # Ajustement de la largeur des colonnes (simplifié)
        for col_idx in range(1, len(headers) + 1):
             column_letter = get_column_letter(col_idx)
             ws.column_dimensions[column_letter].width = 20 # Set a default width

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel CVU sauvegardé localement: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        if drive_url:
            logging.info(f"Excel CVU uploadé sur Drive: {drive_url}")
        else:
            logging.error(f"Échec de l'upload Drive pour Excel CVU: {excel_path}")

    except Exception as e:
        logging.exception(f"Erreur lors de la génération de l'Excel CVU pour {user_id}: {e}")
        drive_url = None # Assurer que l'URL est None en cas d'erreur
    finally:
        # Fermer le classeur s'il est ouvert (évite les erreurs de suppression sous Windows)
        if wb:
             try:
                 wb.close()
             except Exception as close_e:
                 logging.warning(f"Erreur lors de la fermeture du classeur Excel CVU: {close_e}")
        # Nettoyer le fichier local
        if os.path.exists(excel_path):
            try:
                os.remove(excel_path)
                logging.info(f"Fichier local Excel CVU supprimé: {excel_path}")
            except OSError as e:
                logging.error(f"Erreur lors de la suppression du fichier Excel CVU {excel_path}: {e}")

    return drive_url


# --- Function 2: Amortization (Immobilisations) - Simplified ---
def generate_amortization_excel(user_id, immobilisations_list):
    """
    Génère un fichier Excel simplifié pour les immobilisations, l'upload sur Drive et retourne l'URL.
    Expects immobilisations_list to be a list of dictionaries, each with 'description' and 'cost'.
    """
    excel_path = f"immobilisations_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Immobilisations"

        ws['A1'] = "Liste des Immobilisations Enregistrées"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:B1')
        ws['A1'].alignment = Alignment(horizontal='center')

        # En-têtes simplifiés
        headers = ["Description", "Coût d'acquisition $"]
        ws.append(headers) # Append starts from the next available row (A2)

        # Mettre les en-têtes en gras et centrés
        for cell in ws[2]: # La ligne 2 contient les en-têtes
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        # Ajouter les données
        total_cost_all = 0
        for item in immobilisations_list:
            description = item.get('description', 'N/A')
            cost = item.get('cost', 0)
            row = [description, f"{cost:.2f}"]
            ws.append(row)
            total_cost_all += cost

        # Ajouter une ligne pour le total
        ws.append([]) # Ligne vide
        total_row_idx = ws.max_row + 1
        ws.cell(row=total_row_idx, column=1, value="Coût Total Immobilisations").font = Font(bold=True)
        ws.cell(row=total_row_idx, column=2, value=f"{total_cost_all:.2f}").font = Font(bold=True)
        ws.cell(row=total_row_idx, column=2).alignment = Alignment(horizontal='center')


        # Ajuster la largeur des colonnes
        ws.column_dimensions['A'].width = 40 # Description
        ws.column_dimensions['B'].width = 20 # Coût

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel Immobilisations sauvegardé localement: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        if drive_url:
            logging.info(f"Excel Immobilisations uploadé sur Drive: {drive_url}")
        else:
            logging.error(f"Échec de l'upload Drive pour Excel Immobilisations: {excel_path}")

    except Exception as e:
        logging.exception(f"Erreur lors de la génération de l'Excel Immobilisations pour {user_id}: {e}")
        drive_url = None
    finally:
        if wb:
             try:
                 wb.close()
             except Exception as close_e:
                 logging.warning(f"Erreur lors de la fermeture du classeur Excel Immobilisations: {close_e}")
        if os.path.exists(excel_path):
            try:
                os.remove(excel_path)
                logging.info(f"Fichier local Excel Immobilisations supprimé: {excel_path}")
            except OSError as e:
                logging.error(f"Erreur lors de la suppression du fichier Excel Immobilisations {excel_path}: {e}")

    return drive_url


# --- Function 3: Fixed Costs (CFU) ---
def generate_cfu_excel(user_id, cfu_data):
    """
    Génère un fichier Excel pour les coûts fixes (CFU), l'upload sur Drive et retourne l'URL.
    Expects cfu_data to be a dictionary like {'rent': 100, 'salaries': 500, 'others': 50, 'total_cf': 650}.
    """
    excel_path = f"cfu_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Coûts Fixes"

        ws['A1'] = "Calcul des Coûts Fixes (CF) Totaux"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:B1')
        ws['A1'].alignment = Alignment(horizontal='center')

        # Ajouter les données directement (format simple)
        headers = ["Élément du Coût Fixe", "Montant Total $"]
        ws.append(headers)
        for cell in ws[2]: # Ligne 2
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        data_rows = [
            ("Loyer / Charge similaire", cfu_data.get('rent', 0)),
            ("Salaires et Charges Sociales", cfu_data.get('salaries', 0)),
            ("Autres Coûts Fixes", cfu_data.get('others', 0)),
        ]

        for label, amount in data_rows:
            ws.append([label, f"{amount:.2f}"])

        # Ajouter la ligne Total
        ws.append([]) # Ligne vide
        total_row_idx = ws.max_row + 1
        ws.cell(row=total_row_idx, column=1, value="Total Coûts Fixes (CF)").font = Font(bold=True)
        ws.cell(row=total_row_idx, column=2, value=f"{cfu_data.get('total_cf', 0):.2f}").font = Font(bold=True)
        ws.cell(row=total_row_idx, column=2).alignment = Alignment(horizontal='center')


        # Ajuster la largeur des colonnes
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel CFU sauvegardé localement: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        if drive_url:
            logging.info(f"Excel CFU uploadé sur Drive: {drive_url}")
        else:
            logging.error(f"Échec de l'upload Drive pour Excel CFU: {excel_path}")

    except Exception as e:
        logging.exception(f"Erreur lors de la génération de l'Excel CFU pour {user_id}: {e}")
        drive_url = None
    finally:
        if wb:
             try:
                 wb.close()
             except Exception as close_e:
                 logging.warning(f"Erreur lors de la fermeture du classeur Excel CFU: {close_e}")
        if os.path.exists(excel_path):
            try:
                os.remove(excel_path)
                logging.info(f"Fichier local Excel CFU supprimé: {excel_path}")
            except OSError as e:
                logging.error(f"Erreur lors de la suppression du fichier Excel CFU {excel_path}: {e}")

    return drive_url

# --- Function 4: Environment Costs - Corrected/Simplified ---
# Note: The original function had issues. This is a guess based on structure.
# You'll need to adapt it based on what data `env` actually holds.
def generate_costs_env_excel(user_id, env_data_list):
    """
    Génère un fichier Excel pour les coûts environnementaux (exemple), l'upload et retourne l'URL.
    Expects env_data_list to be a list of dictionaries.
    """
    excel_path = f"env_costs_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Coûts Environnementaux"

        ws['A1'] = "Exemple Coûts Environnementaux / Formation"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:C1') # Ajusté à 3 colonnes pour cet exemple
        ws['A1'].alignment = Alignment(horizontal='center')

        headers = ["Description", "Sessions/Unités", "Coût Total $"] # Exemple d'en-têtes
        ws.append(headers)
        for cell in ws[2]: # Ligne 2
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        total_env_cost = 0
        for item in env_data_list:
            # Adaptez ces clés à ce que contient réellement chaque 'item' dans env_data_list
            description = item.get('description', 'Formation/Activité Env.')
            quantity = item.get('quantity', item.get('training_sessions', 0)) # Essayer plusieurs clés possibles
            cost = item.get('total_cost', item.get('training_costs', 0)) # Essayer plusieurs clés possibles
            row = [description, quantity, f"{cost:.2f}"]
            ws.append(row)
            total_env_cost += cost

        # Ajouter la ligne Total
        ws.append([]) # Ligne vide
        total_row_idx = ws.max_row + 1
        ws.cell(row=total_row_idx, column=1, value="Total Coûts Env.").font = Font(bold=True)
        ws.cell(row=total_row_idx, column=3, value=f"{total_env_cost:.2f}").font = Font(bold=True)
        ws.cell(row=total_row_idx, column=3).alignment = Alignment(horizontal='center')


        # Ajuster la largeur des colonnes
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel Coûts Env. sauvegardé localement: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        if drive_url:
            logging.info(f"Excel Coûts Env. uploadé sur Drive: {drive_url}")
        else:
            logging.error(f"Échec de l'upload Drive pour Excel Coûts Env.: {excel_path}")

    except Exception as e:
        logging.exception(f"Erreur lors de la génération de l'Excel Coûts Env. pour {user_id}: {e}")
        drive_url = None
    finally:
        if wb:
             try:
                 wb.close()
             except Exception as close_e:
                 logging.warning(f"Erreur lors de la fermeture du classeur Excel Env: {close_e}")
        if os.path.exists(excel_path):
            try:
                os.remove(excel_path)
                logging.info(f"Fichier local Excel Coûts Env. supprimé: {excel_path}")
            except OSError as e:
                logging.error(f"Erreur lors de la suppression du fichier Excel Coûts Env. {excel_path}: {e}")

    return drive_url