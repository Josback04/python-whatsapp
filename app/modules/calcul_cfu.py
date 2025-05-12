# app/modules/calcul_cfu.py
import logging
# Import the excel generation function
from app.services.excel_service import generate_cfu_excel
# from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

def start_cfu(wa_id):
    # ... (votre code existant) ...
    logging.info(f"Démarrage du module CFU pour {wa_id}")
    response = "Calculons vos Coûts Fixes (CF) totaux.\n\nQuel est le montant de votre loyer (ou charge similaire) pour la période ? (Mettez 0 si non applicable)"
    state = {
        "module": "CFU",
        "step": "ASK_RENT",
        "data": {}
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    # Déplacer les imports nécessaires ici
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    logging.info(f"Traitement CFU pour {wa_id} (step={state.get('step')}): {message_body}")
    step = state.get("step")
    data = state.get("data", {})
    response = "Je n'ai pas compris. Pouvez-vous entrer un montant numérique ?"

    try:
        cost = float(message_body.replace(",", "."))
        if cost < 0:
             response = "Le montant doit être positif ou zéro. Veuillez entrer une valeur correcte."
             state["response"] = response
             return state

        if step == "ASK_RENT":
            data["rent"] = cost
            response = "Compris. Quel est le montant total des salaires et charges sociales fixes pour la période ?"
            state["step"] = "ASK_SALARIES"

        elif step == "ASK_SALARIES":
            data["salaries"] = cost
            response = "Bien noté. Avez-vous d'autres coûts fixes (assurances, abonnements, etc.) ? Si oui, entrez leur montant total, sinon entrez 0."
            state["step"] = "ASK_OTHERS"

        elif step == "ASK_OTHERS":
            data["others"] = cost

            # Calcul final
            total_cf = data.get("rent", 0) + data.get("salaries", 0) + data.get("others", 0)
            data["total_cf"] = total_cf # Stocker le total dans data
            response = f"Calcul terminé ! Le total de vos Coûts Fixes (CF) est de : {total_cf:.2f}.\n\nPréparation de votre fichier Excel..."

            # Envoyer message de calcul + attente
            processing_data = get_text_message_input(wa_id, response)
            send_message(processing_data)

            # Générer Excel et obtenir URL
            drive_url = generate_cfu_excel(wa_id, data) # Passer tout le dict data

            if drive_url:
                final_response = f"Voici le lien vers votre fichier Excel des coûts fixes : {drive_url}"
            else:
                final_response = "Le calcul est terminé, mais une erreur est survenue lors de la création du fichier Excel."

            # Fin du module CFU
            delete_user_state(wa_id)
            return {"module": "FINISHED", "response": final_response}

    except ValueError:
        response = "Montant invalide. Veuillez entrer un nombre (ex: 500 ou 123.45)."

    except Exception as e:
         logging.exception(f"Erreur dans handle_message CFU pour {wa_id}: {e}")
         response = "Désolé, une erreur est survenue."
         delete_user_state(wa_id)
         return {"module": "FINISHED", "response": response + "\n\nRetour au menu principal."}

    state["data"] = data
    state["response"] = response
    return state # Retourner l'état pour continuer si pas fini