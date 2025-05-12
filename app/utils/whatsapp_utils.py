import logging
from flask import current_app, jsonify
import json
import requests
import redis
from app.questions import QUESTIONS
from app.config import redis_client
from app.modules import formulaire, calcul_cvu, calcul_cfu, calcul_immo

# from app.services.openai_service import generate_response
import re 


# Connexion Redis (assure-toi que Redis tourne)
try:
    redis_client 
    redis_client.ping() # Vérifier la connexion
    logging.info("Connexion à Redis réussie.")
except redis.exceptions.ConnectionError as e:
    logging.error(f"Impossible de se connecter à Redis: {e}")
    # Gérer l'erreur comme il convient (ex: arrêter l'app, mode dégradé)
    redis_client = None 

CATEGORY_ORDER = list(QUESTIONS.keys())  # Ordre des catégories

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def generate_response(response):
    # Return text in uppercase
    return response.upper()

def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def get_user_state(wa_id):
    if not redis_client:
        logging.error("Client Redis non disponible")
        return {"module":"ERROR", "message":"Service indisponible"}
    state_json = redis_client.get(wa_id)
    
    if state_json:
        try:
            return json.loads(state_json)
        except json.JSONDecodeError:
            logging.error(f"Erreur de décodage JSON pour l'état de {wa_id}")
            # Retourner un état initial ou d'erreur
            return {"module": None} 
    return {"module": None} # Nouvel utilisateur ou état perdu


def set_user_state(wa_id,state):
    """Sauvegarde l'état de l'utilisateur dans Redis."""
    if not redis_client:
        logging.error("Client Redis non disponible pour set_user_state.")
        return False
        
    try:
        state_json = json.dumps(state)
        redis_client.set(wa_id, state_json)
        # Optionnel : définir une expiration pour nettoyer les états inactifs
        # redis_client.expire(wa_id, 3600) # Expire après 1 heure d'inactivité
        return True
    except TypeError as e:
        logging.error(f"Erreur de sérialisation JSON pour l'état de {wa_id}: {e}")
        return False
    except redis.exceptions.RedisError as e:
         logging.error(f"Erreur Redis lors de set_user_state pour {wa_id}: {e}")
         return False

def delete_user_state(wa_id):
    """Supprime l'état de l'utilisateur de Redis."""
    if not redis_client:
         logging.error("Client Redis non disponible pour delete_user_state.")
         return False
    try:
        redis_client.delete(wa_id)
        return True
    except redis.exceptions.RedisError as e:
         logging.error(f"Erreur Redis lors de delete_user_state pour {wa_id}: {e}")
         return False


# Add this function to app/utils/whatsapp_utils.py

def send_document_message(recipient_id, media_id, caption=None, filename="document.docx"):
    """Sends a document message using a media ID."""
    
    json_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename, # Provide a filename for the user
        }
    }
    # Add caption if provided
    if caption:
        json_data["document"]["caption"] = caption

    data = json.dumps(json_data) # Convert dict to JSON string
    
    # Use your existing send_message infrastructure or call directly
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        log_http_response(response) # Use your existing logging
        logging.info(f"Document message sent successfully to {recipient_id}")
        return True
    except requests.Timeout:
        logging.error(f"Timeout occurred while sending document message to {recipient_id}")
        return False
    except requests.RequestException as e:
        logging.error(f"Request failed sending document to {recipient_id}: {e}")
        log_http_response(e.response) # Log error response if available
        return False
    except Exception as e:
         logging.error(f"Unexpected error sending document to {recipient_id}: {e}")
         return False


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


MAIN_MENU_TEXT = """Bienvenu chez I&F Entrepreneuriat ! 😊 Que souhaitez-vous faire ?

1. 📝 Remplir le formulaire de candidature COPA
2. 📊 Calculer le Coût Variable Unitaire (CVU)
3. 📈 Calculer les Coûts Fixes (CF) 
4. 🏗️ Enregistrer une immobilisation

Répondez par le numéro de votre choix (1, 2, 3 ou 4).
Tapez "menu" à tout moment pour revenir ici.
"""



PROCESSED_MSG_TTL = 300

def process_whatsapp_message(body):
    """
    Traite le message entrant, gère l'état et route vers le module approprié.
    """
    if not redis_client:
        # Envoyer un message d'erreur si Redis n'est pas dispo
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        error_message = "Désolé, une erreur technique nous empêche de traiter votre demande pour le moment. Veuillez réessayer plus tard."
        data = get_text_message_input(wa_id, error_message)
        send_message(data)
        return jsonify({"status": "error", "message": "Redis unavailable"}), 500

    try:
        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        message_id=message["id"]

        processed_key= f"processed_msg:{message_id}"
        if redis_client.exists(processed_key):
            # Message déjà traité dans les 5 minutes
            logging.warning(f"Message {message_id} déjà traité")
            return jsonify({"status": "success", "message": "Message déjà traité"}), 200
        
        if message["type"] != "text":
            logging.info(f"Message de type '{message['type']}' ignoré (ID: {message_id}).")
            redis_client.setex(processed_key, PROCESSED_MSG_TTL, "1")
        
        message_body = message["text"]["body"].strip().lower()


        # Récupérer l'état actuel de l'utilisateur
        user_state = get_user_state(wa_id)
        current_module = user_state.get("module")

        response_text = None
        new_state = user_state.copy() # Travailler sur une copie pour éviter les modifications partielles

        # Commande "menu" ou "restart" pour revenir au menu principal
        if message_body in ["menu", "restart", "accueil"]:
            delete_user_state(wa_id)
            response_text = MAIN_MENU_TEXT
            new_state = {"module": "MENU"} # Mettre l'état explicitement à MENU
        
        # Si l'utilisateur est au menu ou vient d'arriver
        elif current_module is None or current_module == "MENU":
            if message_body == "1":
                new_state = formulaire.start_formulaire(wa_id)
                response_text = new_state.get("response")
            elif message_body == "2":
                new_state = calcul_cvu.start_cvu(wa_id)
                response_text = new_state.get("response")
            elif message_body == "3":
                 new_state = calcul_cfu.start_cfu(wa_id)
                 response_text = new_state.get("response")
            elif message_body == "4":
                 new_state = calcul_immo.start_immos(wa_id)
                 response_text = new_state.get("response")
            else:
                # Si ce n'est pas la première interaction (current_module == "MENU")
                # et que l'entrée est invalide
                if current_module == "MENU":
                     response_text = f"Choix invalide. Veuillez répondre par 1, 2, 3 ou 4.\n\n{MAIN_MENU_TEXT}"
                     new_state["module"] = "MENU" # Rester au menu
                else: # Première interaction (current_module is None)
                    response_text = MAIN_MENU_TEXT
                    new_state = {"module": "MENU"} # Initialiser l'état au menu

        # Router vers le module actif
        elif current_module == "FORMULAIRE":
            new_state = formulaire.handle_message(wa_id, message_body, user_state)
            if new_state is None:
                logging.info(f"formulaire.handle_message returned None for user {wa_id}. Resetting state.")
                response_text="une erreur est survenue. Veuillez réessayer."
                new_state = {"module": "MENU"}
            else:
                response_text = new_state.get("response")
        elif current_module == "CVU":
            new_state = calcul_cvu.handle_message(wa_id, message_body, user_state)
            if new_state is None:
                logging.info(f"formulaire.handle_message returned None for user {wa_id}. Resetting state.")
                response_text="une erreur est survenue. Veuillez réessayer."
                new_state = {"module": "MENU"}
            else:
                response_text = new_state.get("response")

        elif current_module == "CFU":
            new_state = calcul_cfu.handle_message(wa_id, message_body, user_state)
            if new_state is None:
                logging.info(f"formulaire.handle_message returned None for user {wa_id}. Resetting state.")
                response_text="une erreur est survenue. Veuillez réessayer."
                new_state = {"module": "MENU"}
            else:
             response_text = new_state.get("response")

        elif current_module == "IMMOS":
            new_state = calcul_immo.handle_message(wa_id, message_body, user_state)
            if new_state is None:
                logging.info(f"formulaire.handle_message returned None for user {wa_id}. Resetting state.")
                response_text="une erreur est survenue. Veuillez réessayer."
                new_state = {"module": "MENU"}
            else:
                response_text = new_state.get("response")
        
        elif current_module == "ERROR": # Gérer l'état d'erreur Redis précédent
            response_text = user_state.get("message", "Une erreur est survenue.")
            # On pourrait tenter de réinitialiser ici ou juste informer
            delete_user_state(wa_id) # Essayer de nettoyer
        
        else:
            # Module inconnu ou état corrompu, revenir au menu
            logging.warning(f"État inconnu '{current_module}' pour {wa_id}. Réinitialisation au menu.")
            delete_user_state(wa_id)
            response_text = f"Oups, quelque chose s'est mal passé. Revenons au début.\n\n{MAIN_MENU_TEXT}"
            new_state = {"module": "MENU"}


        # Sauvegarder le nouvel état si nécessaire et envoyer la réponse
        if response_text:
             action_taken = False # Flag pour savoir si on a fait une action nécessitant de marquer comme traité
             
             # Si le module est terminé, supprimer l'état
             if new_state.get("module") is None or new_state.get("module") == "FINISHED":
                 delete_user_state(wa_id)
                 final_response = response_text + "\n\nVous pouvez taper 'menu' pour recommencer."
                 data = get_text_message_input(wa_id, final_response)
                 send_message(data)
                 action_taken = True
             # Si on revient au menu explicitement
             elif new_state.get("module") == "MENU":
                set_user_state(wa_id, {"module": "MENU"}) 
                delete_user_state(wa_id)
                response_text += f"\n\n{MAIN_MENU_TEXT}" 
                data = get_text_message_input(wa_id, response_text)
                send_message(data)
                action_taken = True
             # Cas général: sauvegarder l'état et envoyer la réponse du module
             else:
                 # Sauvegarder l'état AVANT d'envoyer potentiellement, pour la cohérence
                 if set_user_state(wa_id, new_state): 
                    data = get_text_message_input(wa_id, response_text)
                    send_message(data)
                    action_taken = True
                 else:
                     # Si la sauvegarde échoue, on ne veut pas marquer comme traité ? Ou si ?
                     # Il vaut mieux marquer comme traité pour éviter boucle, mais logguer l'erreur de sauvegarde
                     logging.error(f"Échec de la sauvegarde de l'état pour {wa_id} après traitement du message {message_id}, mais message envoyé.")
                     action_taken = True # On a quand même essayé d'agir

             # ---- Marquer le message comme traité UNIQUEMENT si une action a été effectuée ----
             if action_taken:
                 try:
                     redis_client.setex(processed_key, PROCESSED_MSG_TTL, "1") # Marquer comme traité
                     logging.info(f"Message ID {message_id} marqué comme traité.")
                 except redis.exceptions.RedisError as e:
                      logging.error(f"Erreur Redis lors du marquage du message {message_id} comme traité: {e}")
                      # Que faire ici? Le message risque d'être retraité. 
                      # Pour l'instant on loggue juste.

        else:
             # Si aucune réponse n'est générée (ex: traitement interne silencieux?), 
             # faut-il marquer comme traité ? Oui, pour éviter les retries inutiles.
             try:
                 redis_client.setex(processed_key, PROCESSED_MSG_TTL, "1")
                 logging.info(f"Message ID {message_id} (sans réponse directe) marqué comme traité.")
             except redis.exceptions.RedisError as e:
                 logging.error(f"Erreur Redis lors du marquage du message {message_id} (sans réponse) comme traité: {e}")


        return jsonify({"status": "ok"}), 200

    except Exception as e:
        # ... (gestion des erreurs inchangée) ...
        logging.exception(f"Erreur inattendue dans process_whatsapp_message: {e}")
        # ... (tentative d'envoyer message d'erreur) ...
        return jsonify({"status": "error", "message": "Internal server error"}), 500

def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
