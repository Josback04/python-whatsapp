# app/modules/calcul_immo.py
import logging
# Import the excel generation function
from app.services.excel_service import generate_amortization_excel
# from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

def start_immos(wa_id):
    logging.info(f"Démarrage du module IMMOS pour {wa_id}")
    response = "Enregistrons une immobilisation.\n\nQuelle est la description de cet actif (ex: Machine X) ?"
    state = {
        "module": "IMMOS",
        "step": "ASK_DESCRIPTION",
        # Stocker les immobilisations dans une liste
        "data": {"immos_list": []}
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    # Déplacer les imports nécessaires ici
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    logging.info(f"Traitement IMMOS pour {wa_id} (step={state.get('step')}): {message_body}")
    step = state.get("step")
    data = state.get("data", {"immos_list": []}) # Assurer que la liste existe
    response = "Je n'ai pas bien compris."

    if step == "ASK_DESCRIPTION":
        # Stocker temporairement la description
        state["current_immo_desc"] = message_body
        response = f"Compris : '{message_body}'.\nQuel est son coût d'acquisition (prix d'achat HT) ?"
        state["step"] = "ASK_COST"

    elif step == "ASK_COST":
        try:
            cost = float(message_body.replace(",", "."))
            if cost <= 0:
                 response = "Le coût d'acquisition doit être positif. Veuillez entrer une valeur correcte."
            else:
                # Ajouter l'immo à la liste dans data
                description = state.get("current_immo_desc", "Inconnue")
                immo_item = {"description": description, "cost": cost}
                data["immos_list"].append(immo_item)

                # Demander si l'utilisateur veut en ajouter une autre ou terminer
                response = (f"Immobilisation '{description}' (Coût: {cost:.2f}) ajoutée.\n\n"
                            "Voulez-vous enregistrer une autre immobilisation ? Répondez 'oui' ou 'non'.")
                state["step"] = "ASK_MORE_IMMOS"
                # Nettoyer la description temporaire
                if "current_immo_desc" in state:
                    del state["current_immo_desc"]

        except ValueError:
             response = "Coût invalide. Veuillez entrer un nombre (ex: 2500.00)."
        except Exception as e:
             logging.exception(f"Erreur inattendue dans ASK_COST IMMOS pour {wa_id}: {e}")
             response = "Désolé, une erreur est survenue."
             delete_user_state(wa_id)
             return {"module": "FINISHED", "response": response + "\n\nRetour au menu."}

    elif step == "ASK_MORE_IMMOS":
        if message_body.lower() == 'oui':
            # Revenir au début pour ajouter une autre
            response = "Quelle est la description du nouvel actif ?"
            state["step"] = "ASK_DESCRIPTION"
        elif message_body.lower() == 'non':
            # Terminer et générer l'Excel
            response = "Enregistrement terminé.\n\nPréparation de votre fichier Excel récapitulatif..."

            # Envoyer message d'attente
            processing_data = get_text_message_input(wa_id, response)
            send_message(processing_data)

            # Générer Excel avec la liste stockée dans data
            drive_url = generate_amortization_excel(wa_id, data["immos_list"])

            if drive_url:
                final_response = f"Voici le lien vers votre fichier Excel des immobilisations : {drive_url}"
            else:
                final_response = "L'enregistrement est terminé, mais une erreur est survenue lors de la création du fichier Excel."

            # Fin du module IMMOS
            delete_user_state(wa_id)
            return {"module": "FINISHED", "response": final_response}
        else:
            # Réponse invalide, redemander
            response = "Veuillez répondre par 'oui' pour ajouter une autre immobilisation, ou 'non' pour terminer."
            # Rester à l'étape ASK_MORE_IMMOS

    # Mettre à jour l'état si on ne retourne pas "FINISHED"
    state["data"] = data
    state["response"] = response
    return state # Retourner l'état pour continuer