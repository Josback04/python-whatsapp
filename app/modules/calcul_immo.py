# app/modules/calcul_immos.py
import logging

def start_immos(wa_id):
    logging.info(f"Démarrage du module IMMOS pour {wa_id}")
    response = "Enregistrons une immobilisation.\n\nQuelle est la description de cet actif (ex: Machine X, Ordinateur portable Y) ?"
    state = {
        "module": "IMMOS",
        "step": "ASK_DESCRIPTION",
        "current_immo": {} # Pour stocker les détails de l'immo en cours
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    logging.info(f"Traitement IMMOS pour {wa_id} (step={state.get('step')}): {message_body}")
    step = state.get("step")
    current_immo = state.get("current_immo", {})
    response = "Je n'ai pas bien compris."

    if step == "ASK_DESCRIPTION":
        current_immo["description"] = message_body
        response = f"Compris : '{message_body}'.\nQuel est son coût d'acquisition (prix d'achat HT) ?"
        state["step"] = "ASK_COST"
    
    elif step == "ASK_COST":
        try:
            cost = float(message_body.replace(",", "."))
            if cost <= 0:
                 response = "Le coût d'acquisition doit être positif. Veuillez entrer une valeur correcte."
            else:
                current_immo["cost"] = cost
                # Pour l'instant, on s'arrête là pour cet exemple simple
                # On pourrait demander date d'achat, durée d'amortissement, etc.
                response = f"Immobilisation enregistrée :\n- Description : {current_immo.get('description')}\n- Coût : {current_immo.get('cost'):.2f}\n\n(Note: ceci est une démo, l'information n'est pas stockée durablement)."
                
                # Fin du module IMMOS (pour cette simple démo)
                state = {"module": "FINISHED", "response": response}
                return state

        except ValueError:
             response = "Coût invalide. Veuillez entrer un nombre (ex: 2500.00)."
        except Exception as e:
             logging.exception(f"Erreur dans handle_message IMMOS pour {wa_id}: {e}")
             response = "Désolé, une erreur est survenue."
             state = {"module": "MENU", "response": response}

    state["current_immo"] = current_immo
    state["response"] = response
    return state