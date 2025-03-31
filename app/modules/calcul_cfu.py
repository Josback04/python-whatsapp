# app/modules/calcul_cfu.py
import logging

def start_cfu(wa_id):
    logging.info(f"Démarrage du module CFU pour {wa_id}")
    response = "Calculons vos Coûts Fixes (CF) totaux.\n\nQuel est le montant de votre loyer (ou charge similaire) pour la période ? (Mettez 0 si non applicable)"
    state = {
        "module": "CFU",
        "step": "ASK_RENT",
        "data": {} # Pour stocker les différents coûts
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    logging.info(f"Traitement CFU pour {wa_id} (step={state.get('step')}): {message_body}")
    step = state.get("step")
    data = state.get("data", {})
    response = "Je n'ai pas compris. Pouvez-vous entrer un montant numérique ?"

    try:
        cost = float(message_body.replace(",", "."))
        if cost < 0:
             response = "Le montant doit être positif ou zéro. Veuillez entrer une valeur correcte."
             # Ne pas changer de step, redemander la même chose
             state["response"] = response
             return state

        if step == "ASK_RENT":
            data["rent"] = cost
            response = "Compris. Quel est le montant total des salaires et charges sociales fixes pour la période ?"
            state["step"] = "ASK_SALARIES"
        
        elif step == "ASK_SALARIES":
            data["salaries"] = cost
            response = "Bien noté. Avez-vous d'autres coûts fixes (assurances, abonnements, amortissements non liés à la production directe, etc.) ? Si oui, entrez leur montant total, sinon entrez 0."
            state["step"] = "ASK_OTHERS"

        elif step == "ASK_OTHERS":
            data["others"] = cost
            
            # Calcul final
            total_cf = data.get("rent", 0) + data.get("salaries", 0) + data.get("others", 0)
            response = f"Calcul terminé ! Le total de vos Coûts Fixes (CF) pour la période est de : {total_cf:.2f}."
            
            # Fin du module CFU
            state = {"module": "FINISHED", "response": response}
            return state
            
    except ValueError:
        response = "Montant invalide. Veuillez entrer un nombre (ex: 500 ou 123.45)."
    
    except Exception as e:
         logging.exception(f"Erreur dans handle_message CFU pour {wa_id}: {e}")
         response = "Désolé, une erreur est survenue."
         state = {"module": "MENU", "response": response}

    state["data"] = data
    state["response"] = response
    return state