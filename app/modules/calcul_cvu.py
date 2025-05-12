# app/modules/calcul_cvu.py
import logging
# Import the excel generation function
from app.services.excel_service import generate_costs_excel
# Import whatsapp utils if needed inside handle_message
# from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

def start_cvu(wa_id):
    # ... (votre code existant) ...
    logging.info(f"Démarrage du module CVU pour {wa_id}")
    response = "Bien sûr ! Commençons le calcul du Coût Variable Unitaire (CVU).\n\nQuel est le montant total de vos coûts variables pour la période considérée (ex: matières premières, consommation directe) ?"
    state = {
        "module": "CVU",
        "step": "ASK_TOTAL_VARIABLE_COSTS",
        # Modifiez ici pour stocker les détails si generate_costs_excel en a besoin
        # Exemple: "data": {"costs_list": [], "total_variable_costs": 0, "units": 0, "cvu": 0}
        "data": {}
    }
    state["response"] = response
    return state

def handle_message(wa_id, message_body, state):
    # Déplacer les imports nécessaires ici
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    logging.info(f"Traitement CVU pour {wa_id} (step={state.get('step')}): {message_body}")
    step = state.get("step")
    data = state.get("data", {})
    response = "Oups, je n'ai pas compris. Pouvez-vous réessayer ?"

    try:
        if step == "ASK_TOTAL_VARIABLE_COSTS":
            total_variable_costs = float(message_body.replace(",", "."))
            if total_variable_costs < 0:
                 response = "Le montant des coûts variables doit être positif. Veuillez entrer une valeur correcte."
            else:
                data["total_variable_costs"] = total_variable_costs
                # Vous pourriez avoir besoin de demander plus de détails ici pour remplir 'costs_list'
                # pour la fonction generate_costs_excel. Simplifions pour l'instant.
                # data["costs_list"] = [{"name": "Coûts Variables Totaux", "total_unit_cost": total_variable_costs}] # Exemple simplifié
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
                    data["cvu"] = cvu # Stocker le résultat
                    response = f"Parfait ! Votre Coût Variable Unitaire (CVU) est de : {cvu:.2f} par unité.\n\nPréparation de votre fichier Excel..."

                    # Envoyer le message de calcul terminé + attente
                    processing_data = get_text_message_input(wa_id, response)
                    send_message(processing_data)

                    # Générer l'Excel et obtenir l'URL Drive
                    # Assurez-vous que 'data' contient ce dont generate_costs_excel a besoin
                    drive_url = generate_costs_excel(wa_id, data)

                    if drive_url:
                        final_response = f"Voici le lien vers votre fichier Excel des coûts variables : {drive_url}"
                    else:
                        final_response = "Le calcul est terminé, mais une erreur est survenue lors de la création du fichier Excel."

                    # Fin du module CVU
                    delete_user_state(wa_id) # Nettoyer l'état
                    return {"module": "FINISHED", "response": final_response}
                else:
                     response = "Une erreur s'est produite dans le calcul. Revenons au début du calcul CVU."
                     state = start_cvu(wa_id)
                     response = state["response"]

    except ValueError:
        if step == "ASK_TOTAL_VARIABLE_COSTS":
            response = "Je n'ai pas compris le montant. Veuillez entrer un nombre (ex: 1500.50)."
        elif step == "ASK_UNITS":
            response = "Je n'ai pas compris le nombre d'unités. Veuillez entrer un nombre entier (ex: 100)."

    except Exception as e:
         logging.exception(f"Erreur dans handle_message CVU pour {wa_id}: {e}")
         response = "Désolé, une erreur est survenue lors du traitement de votre réponse."
         # Supprimer l'état en cas d'erreur grave? Ou juste retourner au menu?
         delete_user_state(wa_id)
         return {"module": "FINISHED", "response": response + "\n\nRetour au menu principal."}


    state["data"] = data
    state["response"] = response # Pour la question suivante si pas fini
    return state # Retourner l'état pour continuer la conversation