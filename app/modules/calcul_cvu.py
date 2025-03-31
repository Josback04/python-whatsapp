# app/modules/calcul_cvu.py
import logging

def start_cvu(wa_id):
    """Initialise l'état pour le module CVU."""
    logging.info(f"Démarrage du module CVU pour {wa_id}")
    response = "Bien sûr ! Commençons le calcul du Coût Variable Unitaire (CVU).\n\nQuel est le montant total de vos coûts variables pour la période considérée (ex: matières premières, consommation directe) ?"
    state = {
        "module": "CVU",
        "step": "ASK_TOTAL_VARIABLE_COSTS",
        "data": {}
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    """Gère un message lorsque l'utilisateur est dans le module CVU."""
    logging.info(f"Traitement CVU pour {wa_id} (step={state.get('step')}): {message_body}")
    step = state.get("step")
    data = state.get("data", {})
    response = "Oups, je n'ai pas compris. Pouvez-vous réessayer ?" # Réponse par défaut

    try:
        if step == "ASK_TOTAL_VARIABLE_COSTS":
            total_variable_costs = float(message_body.replace(",", ".")) # Accepter virgule ou point
            if total_variable_costs < 0:
                 response = "Le montant des coûts variables doit être positif. Veuillez entrer une valeur correcte."
            else:
                data["total_variable_costs"] = total_variable_costs
                response = "Compris. Maintenant, combien d'unités avez-vous produites ou vendues pendant cette période ?"
                state["step"] = "ASK_UNITS"
                
        elif step == "ASK_UNITS":
            units = int(message_body)
            if units <= 0:
                response = "Le nombre d'unités doit être supérieur à zéro. Veuillez entrer une valeur correcte."
            else:
                data["units"] = units
                total_variable_costs = data.get("total_variable_costs")
                
                if total_variable_costs is not None and units > 0:
                    cvu = total_variable_costs / units
                    response = f"Parfait ! Votre Coût Variable Unitaire (CVU) est de : {cvu:.2f} par unité."
                    # Fin du module CVU
                    state = {"module": "FINISHED", "response": response} 
                    return state
                else:
                     response = "Une erreur s'est produite dans le calcul. Revenons au début du calcul CVU."
                     state = start_cvu(wa_id) # Réinitialiser ce module
                     response = state["response"] 

    except ValueError:
        if step == "ASK_TOTAL_VARIABLE_COSTS":
            response = "Je n'ai pas compris le montant. Veuillez entrer un nombre (ex: 1500.50)."
        elif step == "ASK_UNITS":
            response = "Je n'ai pas compris le nombre d'unités. Veuillez entrer un nombre entier (ex: 100)."
        # Garder le même step pour redemander
    
    except Exception as e:
         logging.exception(f"Erreur dans handle_message CVU pour {wa_id}: {e}")
         response = "Désolé, une erreur est survenue lors du traitement de votre réponse."
         state = {"module": "MENU", "response": response} # Revenir au menu en cas d'erreur grave


    state["data"] = data
    state["response"] = response
    return state