# app/modules/calcul_immo.py
import logging
from app.services.excel_service import generate_amortization_excel
# from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

def start_immos(wa_id):
    """Initialise le module Immobilisations."""
    logging.info(f"Démarrage du module IMMOS pour {wa_id}")
    response = "Enregistrons vos immobilisations.\n\nQuel est le nom de la première immobilisation (ex: Machine X) ?"
    state = {
        "module": "IMMOS",
        "step": "ASK_NAME",
        "data": {"items_list": []}, # Pour stocker les immobilisations ajoutées
        "current_item": {} # Pour stocker les détails de l'immo en cours d'ajout
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    """Gère la conversation pour le module Immobilisations."""
    # Imports nécessaires ici
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    step = state.get("step")
    data = state.get("data", {"items_list": []})
    current_item = state.get("current_item", {})
    response = "Je n'ai pas bien compris. Pouvez-vous réessayer ?" # Réponse par défaut

    try:
        if step == "ASK_NAME":
            current_item["name"] = message_body.strip()
            response = f"Compris : '{current_item['name']}'.\nQuel est son coût d'acquisition ($) ?"
            state["step"] = "ASK_COST"

        elif step == "ASK_COST":
            cost = float(message_body.replace(",", "."))
            if cost <= 0:
                 response = "Le coût doit être un nombre positif. Veuillez entrer une valeur correcte."
                 # Rester à l'étape ASK_COST
            else:
                current_item["cost"] = cost
                response = f"Coût : {cost:.2f}$.\nQuelle est sa durée de vie utile en années (ex: 5) ?"
                state["step"] = "ASK_LIFESPAN"

        elif step == "ASK_LIFESPAN":
            lifespan = int(message_body)
            if lifespan <= 0:
                response = "La durée de vie doit être un nombre entier positif d'années. Veuillez entrer une valeur correcte."
                # Rester à l'étape ASK_LIFESPAN
            else:
                current_item["lifespan"] = lifespan
                # Item complet, l'ajouter à la liste
                data["items_list"].append(current_item)
                logging.info(f"Immobilisation ajoutée : {current_item}")
                state["current_item"] = {} # Réinitialiser l'item en cours

                response = (f"Immobilisation '{current_item['name']}' ajoutée (Coût: {current_item['cost']:.2f}$, Durée: {current_item['lifespan']} ans).\n\n"
                            "Voulez-vous ajouter une autre immobilisation ? (oui/non)")
                state["step"] = "ASK_MORE"

        elif step == "ASK_MORE":
            answer = message_body.lower()
            if answer == 'oui':
                response = "Quel est le nom de la nouvelle immobilisation ?"
                state["step"] = "ASK_NAME"
            elif answer == 'non':
                # Terminer et générer l'Excel
                if not data["items_list"]:
                     response = "Aucune immobilisation n'a été enregistrée. Retour au menu."
                     delete_user_state(wa_id)
                     return {"module": "FINISHED", "response": response}

                response = "Enregistrement terminé.\n\nPréparation de votre fichier Excel récapitulatif..."
                processing_data = get_text_message_input(wa_id, response)
                send_message(processing_data) # Envoyer message d'attente

                drive_url = generate_amortization_excel(wa_id, data["items_list"])

                if drive_url:
                    final_response = f"Voici le lien vers votre fichier Excel des immobilisations : {drive_url}"
                else:
                    final_response = "L'enregistrement est terminé, mais une erreur est survenue lors de la création du fichier Excel."

                delete_user_state(wa_id)
                return {"module": "FINISHED", "response": final_response}
            else:
                response = "Veuillez répondre par 'oui' ou 'non'."
                # Rester à l'étape ASK_MORE

    except ValueError:
        if step == "ASK_COST":
            response = "Coût invalide. Veuillez entrer un nombre (ex: 1500.50)."
        elif step == "ASK_LIFESPAN":
            response = "Durée invalide. Veuillez entrer un nombre entier d'années (ex: 5)."
        else:
            response = "Entrée invalide. Veuillez vérifier votre saisie."
        # Rester à l'étape courante pour redemander
    except Exception as e:
        logging.exception(f"Erreur inattendue dans handle_message IMMOS ({step}) pour {wa_id}: {e}")
        response = "Désolé, une erreur interne est survenue."
        delete_user_state(wa_id) # Nettoyer en cas d'erreur grave
        return {"module": "FINISHED", "response": response + "\n\nRetour au menu."}

    # Mettre à jour l'état avant de retourner (si pas terminé)
    state["data"] = data
    state["current_item"] = current_item
    state["response"] = response
    return state