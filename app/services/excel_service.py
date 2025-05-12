# app/services/excel_service.py

import os
import logging
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
# Importez votre fonction d'upload Drive
try:
    from .drive_service import upload_file_to_drive
except ImportError:
    from drive_service import upload_file_to_drive

# --- Fonctions Helpe pour le style ---
def set_header_style(cell):
    cell.font = Font(bold=True, color="FFFFFF") # Texte blanc
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid") # Fond bleu
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))
    cell.border = thin_border

def set_data_style(cell, is_currency=False, is_bold=False):
    cell.alignment = Alignment(horizontal='right' if is_currency else 'left', vertical='center')
    if is_currency:
        cell.number_format = '#,##0.00$' # Format monétaire
    if is_bold:
        cell.font = Font(bold=True)
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))
    cell.border = thin_border

# --- Fonction 1: Coûts Variables (CVU) - Mise à jour ---
def generate_costs_excel(user_id, items_list, total_qte_produced):
    """
    Génère Excel CVU basé sur la nouvelle logique, upload et retourne l'URL.
    items_list: [{'name': str, 'global_kg': float, 'global_pt': float}, ...]
    total_qte_produced: float
    """
    excel_path = f"costs_cvu_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None

    if total_qte_produced == 0: # Éviter division par zéro
        logging.error("total_qte_produced is zero, cannot calculate CVU.")
        return None

    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Coût Variable Unitaire"

        # Titre principal
        ws['A1'] = "Calcul du Coût Variable Unitaire (CVU)"
        ws.merge_cells('A1:F1') # Fusionner sur 6 colonnes
        ws['A1'].font = Font(size=14, bold=True)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

        # En-têtes
        headers = ["Élément du CV", "Qté Globale (Kg)", "Prix Total Global ($)", "Prix Unitaire Matière ($/Kg)", "Qté Unitaire (Kg/unité)", "Montant ($/unité)"]
        header_row_num = 3
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row_num, column=col_num, value=header)
            set_header_style(cell)

        # Remplissage des données et calculs
        current_row = header_row_num + 1
        total_cvu = 0.0
        calculated_items = []

        for item in items_list:
            name = item.get('name', 'N/A')
            global_kg = item.get('global_kg', 0.0)
            global_pt = item.get('global_pt', 0.0)

            cost_per_unit_kg = (global_pt / global_kg) if global_kg != 0 else 0
            kg_per_final_unit = global_kg / total_qte_produced
            cost_per_final_unit = global_pt / total_qte_produced # = cost_per_unit_kg * kg_per_final_unit

            calculated_items.append({
                 "name": name,
                 "global_kg": global_kg,
                 "global_pt": global_pt,
                 "cost_per_unit_kg": cost_per_unit_kg,
                 "kg_per_final_unit": kg_per_final_unit,
                 "cost_per_final_unit": cost_per_final_unit
            })
            total_cvu += cost_per_final_unit

            # Écrire dans le fichier Excel
            ws.cell(row=current_row, column=1, value=name)
            ws.cell(row=current_row, column=2, value=global_kg)
            ws.cell(row=current_row, column=3, value=global_pt)
            ws.cell(row=current_row, column=4, value=cost_per_unit_kg)
            ws.cell(row=current_row, column=5, value=kg_per_final_unit)
            ws.cell(row=current_row, column=6, value=cost_per_final_unit)

            # Appliquer le style aux données
            for col_num in range(1, 7):
                 cell = ws.cell(row=current_row, column=col_num)
                 is_currency = col_num in [3, 4, 6]
                 set_data_style(cell, is_currency=is_currency)
                 if col_num in [5]: # Style pour quantité unitaire
                      cell.number_format = '0.00000'

            current_row += 1

        # Ligne Total
        ws.cell(row=current_row, column=1, value="Total Coût Variable Unitaire (CVU)").font = Font(bold=True)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5)
        total_cell = ws.cell(row=current_row, column=6, value=total_cvu)
        set_data_style(total_cell, is_currency=True, is_bold=True)

        # Ajuster largeur colonnes
        column_widths = {'A': 30, 'B': 18, 'C': 20, 'D': 25, 'E': 25, 'F': 20}
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel CVU sauvegardé: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        # ... (logging succès/échec upload)

    except Exception as e:
        logging.exception(f"Erreur génération Excel CVU pour {user_id}: {e}")
        drive_url = None
    finally:
        # ... (fermeture wb et suppression fichier local) ...
        if wb:
             try: wb.close()
             except Exception: pass
        if os.path.exists(excel_path):
            try: os.remove(excel_path)
            except OSError as e: logging.error(f"Erreur suppression {excel_path}: {e}")

    return drive_url


# --- Fonction 2: Immobilisations - Mise à jour ---
def generate_amortization_excel(user_id, items_list):
    """
    Génère Excel Immobilisations avec amortissement, upload et retourne l'URL.
    items_list: [{'name': str, 'cost': float, 'lifespan': int (years)}, ...]
    """
    excel_path = f"immobilisations_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None

    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Amortissement Immobilisations"

        ws['A1'] = "Tableau d'Amortissement Linéaire des Immobilisations"
        ws.merge_cells('A1:E1') # 5 colonnes
        ws['A1'].font = Font(size=14, bold=True)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

        headers = ["Immobilisation (Nom)", "Coût Acquisition ($)", "Durée (ans)", "Amortissement Annuel ($)", "Amortissement Cumulé ($)"]
        header_row_num = 3
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row_num, column=col_num, value=header)
            set_header_style(cell)

        current_row = header_row_num + 1
        total_annual_amortization = 0.0
        calculated_items = []

        for item in items_list:
            name = item.get('name', 'N/A')
            cost = item.get('cost', 0.0)
            lifespan = item.get('lifespan', 0) # Durée en années

            annual_amortization = (cost / lifespan) if lifespan > 0 else 0
            total_annual_amortization += annual_amortization

            # Note: Amortissement cumulé n'a de sens que sur plusieurs années.
            # Ici, on affiche juste le total annuel pour toutes les immobilisations.
            # Si vous voulez un vrai tableau d'amortissement sur N années, c'est plus complexe.

            calculated_items.append({
                 "name": name,
                 "cost": cost,
                 "lifespan": lifespan,
                 "annual_amortization": annual_amortization
            })

            ws.cell(row=current_row, column=1, value=name)
            ws.cell(row=current_row, column=2, value=cost)
            ws.cell(row=current_row, column=3, value=lifespan)
            ws.cell(row=current_row, column=4, value=annual_amortization)
            # Laissez la colonne E vide pour l'instant ou répétez l'amort. annuel
            ws.cell(row=current_row, column=5, value=annual_amortization) # Exemple: affiche amort. annuel ici aussi

            # Appliquer style
            for col_num in range(1, 6):
                 cell = ws.cell(row=current_row, column=col_num)
                 is_currency = col_num in [2, 4, 5]
                 is_int = col_num == 3
                 set_data_style(cell, is_currency=is_currency)
                 if is_int: cell.number_format = '0'


            current_row += 1

        # Ligne Total
        ws.cell(row=current_row, column=1, value="Total Amortissement Annuel").font = Font(bold=True)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
        total_cell_annuel = ws.cell(row=current_row, column=4, value=total_annual_amortization)
        set_data_style(total_cell_annuel, is_currency=True, is_bold=True)
        # Mettre aussi dans la colonne E pour l'alignement visuel
        total_cell_cumul = ws.cell(row=current_row, column=5, value=total_annual_amortization)
        set_data_style(total_cell_cumul, is_currency=True, is_bold=True)


        # Ajuster largeur
        column_widths = {'A': 35, 'B': 20, 'C': 15, 'D': 25, 'E': 25}
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel Amortissement sauvegardé: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        # ... (logging succès/échec upload)

    except Exception as e:
        logging.exception(f"Erreur génération Excel Amortissement pour {user_id}: {e}")
        drive_url = None
    finally:
        # ... (fermeture wb et suppression fichier local) ...
        if wb:
             try: wb.close()
             except Exception: pass
        if os.path.exists(excel_path):
            try: os.remove(excel_path)
            except OSError as e: logging.error(f"Erreur suppression {excel_path}: {e}")

    return drive_url


# --- Fonction 3: Coûts Fixes (CFU) - Mise à jour ---
def generate_cfu_excel(user_id, items_list):
    """
    Génère Excel Coûts Fixes annualisés, upload et retourne l'URL.
    items_list: [{'name': str, 'cost_per_period': float, 'period_months': int}, ...]
    """
    excel_path = f"cfu_{user_id}_{os.urandom(4).hex()}.xlsx"
    drive_url = None
    wb = None

    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Coûts Fixes Annualisés"

        ws['A1'] = "Tableau des Coûts Fixes Annualisés"
        ws.merge_cells('A1:E1') # 5 colonnes
        ws['A1'].font = Font(size=14, bold=True)
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

        headers = ["Coût Fixe (Nom)", "Coût par Période ($)", "Période (mois)", "Facteur Annuel", "Coût Annuel ($)"]
        header_row_num = 3
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row_num, column=col_num, value=header)
            set_header_style(cell)

        current_row = header_row_num + 1
        total_annual_fixed_cost = 0.0
        calculated_items = []

        for item in items_list:
            name = item.get('name', 'N/A')
            cost_per_period = item.get('cost_per_period', 0.0)
            period_months = item.get('period_months', 0)

            annual_factor = (12 / period_months) if period_months > 0 else 0
            annual_cost = cost_per_period * annual_factor
            total_annual_fixed_cost += annual_cost

            calculated_items.append({
                "name": name,
                "cost_per_period": cost_per_period,
                "period_months": period_months,
                "annual_factor": annual_factor,
                "annual_cost": annual_cost
            })

            ws.cell(row=current_row, column=1, value=name)
            ws.cell(row=current_row, column=2, value=cost_per_period)
            ws.cell(row=current_row, column=3, value=period_months)
            ws.cell(row=current_row, column=4, value=annual_factor)
            ws.cell(row=current_row, column=5, value=annual_cost)

            # Style
            for col_num in range(1, 6):
                 cell = ws.cell(row=current_row, column=col_num)
                 is_currency = col_num in [2, 5]
                 is_int = col_num == 3
                 is_factor = col_num == 4
                 set_data_style(cell, is_currency=is_currency)
                 if is_int: cell.number_format = '0'
                 if is_factor: cell.number_format = '0.00'


            current_row += 1

        # Ligne Total
        ws.cell(row=current_row, column=1, value="Total Coûts Fixes Annuels").font = Font(bold=True)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=4)
        total_cell = ws.cell(row=current_row, column=5, value=total_annual_fixed_cost)
        set_data_style(total_cell, is_currency=True, is_bold=True)

        # Ajuster largeur
        column_widths = {'A': 35, 'B': 20, 'C': 15, 'D': 18, 'E': 20}
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Sauvegarde et Upload
        wb.save(excel_path)
        logging.info(f"Excel CFU sauvegardé: {excel_path}")
        drive_url = upload_file_to_drive(excel_path)
        # ... (logging succès/échec upload)

    except Exception as e:
        logging.exception(f"Erreur génération Excel CFU pour {user_id}: {e}")
        drive_url = None
    finally:
        # ... (fermeture wb et suppression fichier local) ...
        if wb:
             try: wb.close()
             except Exception: pass
        if os.path.exists(excel_path):
            try: os.remove(excel_path)
            except OSError as e: logging.error(f"Erreur suppression {excel_path}: {e}")

    return drive_url

# Note: La fonction generate_costs_env_excel n'est pas mise à jour car son objectif
# et la structure de ses données d'entrée ('env') n'étaient pas clairs.
# Si vous en avez besoin, veuillez clarifier ce qu'elle doit calculer et afficher.