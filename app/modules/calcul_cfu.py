# app/modules/calcul_cfu.py
import logging
from app.services.excel_service import generate_cfu_excel
# from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state
from app.database.database import log_usage_event

def start_cfu(wa_id):
    """Initialise le module CFU."""
    logging.info(f"Démarrage du module CFU pour {wa_id}")
    response = ("Calculons vos Coûts Fixes Annualisés.\n\n"
                "Entrez le nom du premier coût fixe (ex: Loyer, Salaire Admin, Abonnement Internet):")
    state = {
        "module": "CFU",
        "step": "ASK_ITEM_NAME",
        "data": {"items_list": []},
        "current_item": {}
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    """Gère la conversation pour le module CFU."""
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    step = state.get("step")
    data = state.get("data", {"items_list": []})
    current_item = state.get("current_item", {})
    response = "Je n'ai pas bien compris. Pouvez-vous réessayer ?"

    try:
        if step == "ASK_ITEM_NAME":
            current_item["name"] = message_body.strip()
            response = f"Coût Fixe : '{current_item['name']}'.\nQuel est le montant ($) payé par période pour ce coût ? (ex: 500)"
            state["step"] = "ASK_COST_PER_PERIOD"

        elif step == "ASK_COST_PER_PERIOD":
            cost = float(message_body.replace(",", "."))
            if cost < 0:
                response = "Le coût ne peut pas être négatif. Entrez une valeur correcte."
            else:
                current_item["cost_per_period"] = cost
                response = (f"Montant : {cost:.2f}$.\n"
                            "Ce montant couvre quelle période ? Entrez le nombre de mois (ex: 1 pour mensuel, 3 pour trimestriel, 12 pour annuel):")
                state["step"] = "ASK_PERIOD_MONTHS"

        elif step == "ASK_PERIOD_MONTHS":
            months = int(message_body)
            if months <= 0 or months > 1200: # Ajouter une limite supérieure raisonnable
                 response = "La période doit être un nombre de mois positif (généralement entre 1 et 12). Veuillez corriger."
            else:
                current_item["period_months"] = months
                # Item complet, ajouter à la liste
                data["items_list"].append(current_item)
                logging.info(f"Élément CFU ajouté : {current_item}")
                state["current_item"] = {} # Réinitialiser

                response = (f"Coût Fixe '{current_item['name']}' ajouté (Coût: {current_item['cost_per_period']:.2f}$ / {current_item['period_months']} mois).\n\n"
                            "Voulez-vous ajouter un autre coût fixe ? (oui/non)")
                state["step"] = "ASK_MORE_ITEMS"

        elif step == "ASK_MORE_ITEMS":
            answer = message_body.lower()
            if answer == 'oui':
                response = "Quel est le nom du nouveau coût fixe ?"
                state["step"] = "ASK_ITEM_NAME"
            elif answer == 'non':
                if not data["items_list"]:
                     response = "Aucun coût fixe n'a été enregistré. Retour au menu."
                     delete_user_state(wa_id)
                     return {"module": "FINISHED", "response": response}

                # Terminer et générer l'Excel
                response = "Enregistrement terminé.\n\nPréparation de votre fichier Excel récapitulatif des coûts fixes annualisés..."
                processing_data = get_text_message_input(wa_id, response)
                send_message(processing_data)

                drive_url = generate_cfu_excel(wa_id, data["items_list"])

                if drive_url:
                    final_response = f"Voici le lien vers votre fichier Excel des coûts fixes annualisés : {drive_url}"
                    log_usage_event(wa_id, "MODULE_COMPLETE", "CFU_FINISHED")
                else:
                    final_response = "L'enregistrement est terminé, mais une erreur est survenue lors de la création du fichier Excel."
                    log_usage_event(wa_id, "MODULE_FAILED", "CFU_FAILED")

                delete_user_state(wa_id)
                return {"module": "FINISHED", "response": final_response}
            else:
                response = "Veuillez répondre par 'oui' ou 'non'."
                # Rester à l'étape ASK_MORE_ITEMS

    except ValueError:
        if step == "ASK_COST_PER_PERIOD":
            response = "Coût invalide. Veuillez entrer un nombre (ex: 500 ou 150.75)."
        elif step == "ASK_PERIOD_MONTHS":
             response = "Période invalide. Veuillez entrer un nombre entier de mois (ex: 1, 3, 12)."
        else:
            response = "Entrée invalide. Veuillez vérifier votre saisie."
        # Rester à l'étape courante
    except Exception as e:
        logging.exception(f"Erreur inattendue dans handle_message CFU ({step}) pour {wa_id}: {e}")
        response = "Désolé, une erreur interne est survenue."
        delete_user_state(wa_id)
        return {"module": "FINISHED", "response": response + "\n\nRetour au menu."}

    state["data"] = data
    state["current_item"] = current_item
    state["response"] = response
    return state