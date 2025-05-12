# app/modules/formulaire.py
import logging
from app.questions import QUESTIONS # Importer les questions
from app.database.database import save_response_to_db
from app.services.gemini import ask_ai
from app.services.docx_service import generate_docx
CATEGORY_ORDER = list(QUESTIONS.keys())

def start_formulaire(wa_id):
    """Initialise l'état pour le module formulaire."""
    logging.info(f"Démarrage du module FORMULAIRE pour {wa_id}")
    category_index = 0
    question_index = 0
    current_category = CATEGORY_ORDER[category_index]
    response = QUESTIONS[current_category][question_index]
    
    # Le premier message est spécial (Bienvenue), on peut l'adapter si besoin
    response = f"Commençons le formulaire ! 😊\n\n{response}" 

    state = {
        "module": "FORMULAIRE",
        "category_index": category_index,
        "question_index": question_index,
    }
    state["response"] = response # Ajouter la réponse à envoyer dans l'état retourné
    return state

def handle_message(wa_id, message_body, state):
    """Gère un message lorsque l'utilisateur est dans le module formulaire."""

    from app.utils.whatsapp_utils import  send_message, get_text_message_input, delete_user_state

    logging.info(f"Traitement FORMULAIRE pour {wa_id}: {message_body}")
    
    category_index = state.get("category_index", 0)
    question_index = state.get("question_index", 0)
    current_category = CATEGORY_ORDER[category_index]

    # *** SAUVEGARDE EN BASE DE DONNÉES ***
    # Récupérer le texte de la question à laquelle l'utilisateur vient de répondre
    try:
        question_asked = QUESTIONS[current_category][question_index]
        # Sauvegarder la réponse de l'utilisateur (message_body) pour la question posée
        save_response_to_db(wa_id, question_asked, message_body)
        # Si la sauvegarde échoue, on loggue l'erreur mais on continue le flux normal
    except IndexError:
        logging.error(f"IndexError lors de la récupération de la question pour la sauvegarde DB: cat={current_category}, index={question_index}")
    except Exception as e:
         logging.exception(f"Erreur inattendue lors de la sauvegarde DB pour {wa_id}: {e}")
    # **************************************

    # Passer à la question suivante (logique existante)
    
    # Optionnel: Sauvegarder la réponse précédente
    # question_key = f"{current_category}_{question_index}"
    # state.setdefault("responses", {})[question_key] = message_body

    # Passer à la question suivante
    question_index += 1

    if question_index >= len(QUESTIONS[current_category]):
        # Passer à la catégorie suivante
        category_index += 1
        question_index = 0
        if category_index >= len(CATEGORY_ORDER):
            # Fin du formulaire
            response = "Merci d'avoir répondu à toutes les questions du formulaire ! 😊"
            # Indiquer la fin pour que le routeur supprime l'état

            state = {"module": "FINISHED", "response": response}

            # Send generating message first
            try:
            # Call AI (as before)
                ai_response = ask_ai(wa_id)
                
                # Generate and upload the document
                # Pass a filename to be shown to the user
                doc_filename = f"PLAN_AFFAIRE_{wa_id}.docx" 
                generate_docx(doc_filename, ai_response)

               

            except Exception as e:
                logging.exception(f"Error during final document generation/sending for {wa_id}: {e}")
                # Send generic error message
                error_response = "Une erreur inattendue s'est produite. Veuillez réessayer."
                error_data = get_text_message_input(wa_id, error_response)
                send_message(error_data)
                state = {"module": "FINISHED", "response": None} # End interaction
        
        return state # Return the final state
