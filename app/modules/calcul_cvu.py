# app/modules/calcul_cvu.py
import logging
from app.services.excel_service import generate_costs_excel
# from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

def start_cvu(wa_id):
    """Initialise le module CVU."""
    logging.info(f"Démarrage du module CVU pour {wa_id}")
    response = ("Calculons votre Coût Variable Unitaire (CVU).\n\n"
                "Entrez le nom du premier élément de coût variable (ex: Farine, Sucre, Emballage):")
    state = {
        "module": "CVU",
        "step": "ASK_ITEM_NAME",
        "data": {
            "items_list": [],
            "total_qte_produced": None # Sera demandé à la fin
        },
        "current_item": {}
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    """Gère la conversation pour le module CVU."""
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    step = state.get("step")
    data = state.get("data", {"items_list": [], "total_qte_produced": None})
    current_item = state.get("current_item", {})
    response = "Je n'ai pas bien compris. Pouvez-vous réessayer ?"

    try:
        if step == "ASK_ITEM_NAME":
            current_item["name"] = message_body.strip()
            response = (f"Élément : '{current_item['name']}'.\n"
                        "Quelle est la quantité globale achetée pour cet élément ? "
                        "(Entrez juste le nombre, ex: 50 pour 50Kg, 10 pour 10 litres)")
            state["step"] = "ASK_GLOBAL_KG" # Nommé KG mais peut être Litre, etc.

        elif step == "ASK_GLOBAL_KG":
            global_kg = float(message_body.replace(",", "."))
            if global_kg <= 0:
                response = "La quantité globale doit être un nombre positif. Veuillez entrer une valeur correcte."
            else:
                current_item["global_kg"] = global_kg
                # On pourrait demander l'unité ici si nécessaire
                # current_item["unit"] = "Kg" # Ou demander à l'user
                response = (f"Quantité globale : {global_kg}.\n"
                            "Quel est le prix total ($) payé pour cette quantité globale ? (ex: 45)")
                state["step"] = "ASK_GLOBAL_PT"

        elif step == "ASK_GLOBAL_PT":
            global_pt = float(message_body.replace(",", "."))
            if global_pt < 0: # Le prix peut être 0 ? On l'autorise.
                 response = "Le prix total ne peut pas être négatif. Veuillez entrer une valeur correcte (ou 0)."
            else:
                current_item["global_pt"] = global_pt
                # Item complet, ajouter à la liste
                data["items_list"].append(current_item)
                logging.info(f"Élément CVU ajouté : {current_item}")
                state["current_item"] = {} # Réinitialiser

                response = (f"Élément '{current_item['name']}' ajouté (Qté: {current_item['global_kg']}, Prix Total: {current_item['global_pt']:.2f}$).\n\n"
                            "Voulez-vous ajouter un autre élément de coût variable ? (oui/non)")
                state["step"] = "ASK_MORE_ITEMS"

        elif step == "ASK_MORE_ITEMS":
            answer = message_body.lower()
            if answer == 'oui':
                response = "Quel est le nom du nouvel élément de coût variable ?"
                state["step"] = "ASK_ITEM_NAME"
            elif answer == 'non':
                if not data["items_list"]:
                     response = "Aucun élément de coût n'a été enregistré. Retour au menu."
                     delete_user_state(wa_id)
                     return {"module": "FINISHED", "response": response}

                # Passer à la question sur la production totale
                response = "Compris. Maintenant, quelle est la quantité totale d'unités que vous pouvez produire avec ces quantités globales de matières premières ? (ex: 100 pour 1000 pains)"
                state["step"] = "ASK_TOTAL_QTE"
            else:
                response = "Veuillez répondre par 'oui' ou 'non'."
                # Rester à l'étape ASK_MORE_ITEMS

        elif step == "ASK_TOTAL_QTE":
            total_qte = float(message_body.replace(",", "."))
            if total_qte <= 0:
                response = "La quantité totale produite doit être positive. Entrez une valeur correcte (ex: 1000)."
            else:
                data["total_qte_produced"] = total_qte
                state["step"] = "PROCESS_FINAL" # Marquer pour traitement final

                response = "Calculs en cours et préparation de votre fichier Excel..."
                processing_data = get_text_message_input(wa_id, response)
                send_message(processing_data)

                # Appel de la fonction Excel
                drive_url = generate_costs_excel(wa_id, data["items_list"], data["total_qte_produced"])

                if drive_url:
                    final_response = f"Voici le lien vers votre fichier Excel de calcul du CVU : {drive_url}"
                else:
                    final_response = ("Le calcul est terminé, mais une erreur est survenue lors de la création du fichier Excel. "
                                      "Vérifiez notamment que la quantité produite n'est pas nulle.")

                delete_user_state(wa_id)
                return {"module": "FINISHED", "response": final_response}


    except ValueError:
        if step == "ASK_GLOBAL_KG":
            response = "Quantité globale invalide. Veuillez entrer un nombre (ex: 50)."
        elif step == "ASK_GLOBAL_PT":
            response = "Prix total invalide. Veuillez entrer un nombre (ex: 45 ou 120.50)."
        elif step == "ASK_TOTAL_QTE":
            response = "Quantité totale produite invalide. Veuillez entrer un nombre (ex: 1000)."
        else:
            response = "Entrée invalide. Veuillez vérifier votre saisie."
         # Rester à l'étape courante
    except Exception as e:
        logging.exception(f"Erreur inattendue dans handle_message CVU ({step}) pour {wa_id}: {e}")
        response = "Désolé, une erreur interne est survenue."
        delete_user_state(wa_id)
        return {"module": "FINISHED", "response": response + "\n\nRetour au menu."}

    state["data"] = data
    state["current_item"] = current_item
    state["response"] = response
    return state