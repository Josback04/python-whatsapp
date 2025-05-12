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
    # Déplacer les imports nécessaires ici pour éviter l'import circulaire
    from app.utils.whatsapp_utils import send_message, get_text_message_input, delete_user_state

    logging.info(f"Traitement FORMULAIRE pour {wa_id}: {message_body}")
    
    category_index = state.get("category_index", 0)
    question_index = state.get("question_index", 0)
    
    # Gérer les cas où l'état pourrait être corrompu (indices invalides)
    try:
        current_category = CATEGORY_ORDER[category_index]
        # Vérifier aussi si la catégorie existe dans QUESTIONS
        if current_category not in QUESTIONS:
             raise IndexError(f"Catégorie '{current_category}' non trouvée dans QUESTIONS.")
        # Vérifier si l'index de question est valide pour la catégorie courante
        if question_index >= len(QUESTIONS[current_category]):
             logging.warning(f"Index de question {question_index} invalide pour catégorie {current_category} au début de handle_message pour {wa_id}. Réinitialisation.")
             # Si l'index est déjà invalide, on ne peut pas sauvegarder la réponse, passer à la suite logique (catégorie suivante ou fin)
             pass # La logique plus bas gérera le passage à la cat. suivante ou la fin
        else:
            # Sauvegarde en base de données (uniquement si les indices sont valides)
             try:
                 question_asked = QUESTIONS[current_category][question_index]
                 save_response_to_db(wa_id, question_asked, message_body)
             except Exception as e:
                 logging.exception(f"Erreur inattendue lors de la sauvegarde DB pour {wa_id}: {e}")

    except IndexError as e:
        logging.error(f"État invalide détecté (IndexError: {e}) pour l'utilisateur {wa_id}. Réinitialisation.")
        delete_user_state(wa_id)
        error_response = "Une erreur est survenue avec votre session. Veuillez recommencer en tapant 'menu'."
        error_data = get_text_message_input(wa_id, error_response)
        send_message(error_data) # Envoyer le message d'erreur immédiatement
        return {"module": "FINISHED", "response": None} # Terminer cette interaction

    # Passer à la question suivante (index)
    question_index += 1

    # Vérifier si la catégorie est terminée
    if question_index >= len(QUESTIONS.get(current_category, [])): 
        # Passer à la catégorie suivante
        category_index += 1
        question_index = 0 # Réinitialiser l'index de question

        # Vérifier si le formulaire est terminé
        if category_index >= len(CATEGORY_ORDER):
            # ---> FIN DU FORMULAIRE <---
            
            # 1. Envoyer un message d'attente IMMÉDIATEMENT
            processing_response = "Merci d'avoir répondu à toutes les questions ! 😊 Votre document est en cours de préparation et de sauvegarde..."
            processing_data = get_text_message_input(wa_id, processing_response)
            if not send_message(processing_data):
                 logging.error(f"Échec de l'envoi du message d'attente à {wa_id}")
                 # Que faire ici? Continuer quand même ou abandonner? Décidons de continuer.

            final_response_text = None # Variable pour stocker le message final (lien ou erreur)
            try:
                # 2. Appeler l'IA
                logging.info(f"Appel de l'IA pour l'utilisateur {wa_id}")
                ai_response = ask_ai(wa_id)

                # 3. Générer le DOCX et l'uploader sur Drive (capturer l'URL)
                logging.info(f"Génération/upload du document pour l'utilisateur {wa_id}")
                # generate_docx appelle upload_file_to_drive et retourne l'URL ou None
                drive_url = generate_docx(wa_id, ai_response) 

                # 4. Vérifier le résultat et préparer la réponse finale
                if drive_url:
                    logging.info(f"Document généré et uploadé pour {wa_id}. URL: {drive_url}")
                    final_response_text = f"Votre document a été généré avec succès ! Vous pouvez le consulter ici : {drive_url}"
                else:
                    logging.error(f"La génération/upload du document a échoué pour l'utilisateur {wa_id}.")
                    final_response_text = "Désolé, une erreur est survenue lors de la création ou de la sauvegarde de votre document. Veuillez réessayer plus tard ou contacter le support."

            except Exception as e:
                logging.exception(f"Erreur lors de la génération/upload du document final pour {wa_id}: {e}")
                final_response_text = "Une erreur inattendue s'est produite lors de la finalisation de votre demande."

            # 5. Renvoyer l'état final pour que le message (lien ou erreur) soit envoyé
            # Supprimer l'état Redis car le processus est terminé (succès ou échec)
            delete_user_state(wa_id) 
            # Le module est terminé, la réponse contient le message final à envoyer
            return {"module": "FINISHED", "response": final_response_text} 

        else: # ---> CATÉGORIE SUIVANTE <---
             try:
                 current_category = CATEGORY_ORDER[category_index]
                 # S'assurer que la nouvelle catégorie est valide
                 if current_category not in QUESTIONS or not QUESTIONS[current_category]:
                     raise ValueError(f"La catégorie '{current_category}' est vide ou invalide.")
                 
                 response = QUESTIONS[current_category][question_index] # Première question de la nouvelle catégorie
                 state["category_index"] = category_index
                 state["question_index"] = question_index
                 state["response"] = response
                 # Retourner l'état mis à jour pour poser la nouvelle question
                 return state
             except (IndexError, ValueError) as e:
                 logging.error(f"Erreur lors du passage à la catégorie {category_index} pour {wa_id}: {e}")
                 delete_user_state(wa_id)
                 error_response = "Une erreur est survenue lors du passage à la section suivante. Veuillez recommencer en tapant 'menu'."
                 error_data = get_text_message_input(wa_id, error_response)
                 send_message(error_data)
                 return {"module": "FINISHED", "response": None}

    else: # ---> QUESTION SUIVANTE (même catégorie) <---
         try:
             response = QUESTIONS[current_category][question_index]
             state["question_index"] = question_index
             state["response"] = response
             # Retourner l'état mis à jour pour poser la question suivante
             return state
         except IndexError:
              logging.error(f"État invalide: index de question {question_index} hors limites pour catégorie {current_category} ({wa_id}).")
              delete_user_state(wa_id)
              error_response = "Une erreur est survenue lors du passage à la question suivante. Veuillez recommencer en tapant 'menu'."
              error_data = get_text_message_input(wa_id, error_response)
              send_message(error_data)
              return {"module": "FINISHED", "response": None}