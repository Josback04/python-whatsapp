import logging
from flask import current_app, jsonify
import json
import requests
import redis
from app.questions import QUESTIONS

# from app.services.openai_service import generate_response
import re 


# Connexion Redis (assure-toi que Redis tourne)
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)


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


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    message_body = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

    current_category = redis_client.hget(wa_id, "current_category")
    current_question_index = redis_client.hget(wa_id, "current_question_index")

    if current_category is None or current_question_index is None:  # Début de la discussion
        current_category = CATEGORY_ORDER[0]
        current_question_index = 0
        redis_client.hset(wa_id, "current_category", current_category)
        redis_client.hset(wa_id, "current_question_index", current_question_index)
        response = QUESTIONS[current_category][current_question_index]
    else:
        current_question_index = int(current_question_index) + 1

        if current_question_index >= len(QUESTIONS[current_category]):  # Passer à la catégorie suivante
            category_index = CATEGORY_ORDER.index(current_category) + 1
            if category_index >= len(CATEGORY_ORDER):  # Fin des questions
                response = "Merci d'avoir répondu à toutes les questions ! 😊"
                redis_client.delete(wa_id)  # Supprime l'historique de l'utilisateur
            else:
                current_category = CATEGORY_ORDER[category_index]
                current_question_index = 0
                redis_client.hset(wa_id, "current_category", current_category)
                redis_client.hset(wa_id, "current_question_index", current_question_index)
                response = QUESTIONS[current_category][current_question_index]
        else:
            redis_client.hset(wa_id, "current_question_index", current_question_index)
            response = QUESTIONS[current_category][current_question_index]

    # Réinitialisation si l'utilisateur tape "restart"
    if message_body.lower() == "restart":
        redis_client.delete(wa_id)
        current_category = CATEGORY_ORDER[0]
        current_question_index = 0
        redis_client.hset(wa_id, "current_category", current_category)
        redis_client.hset(wa_id, "current_question_index", current_question_index)
        response = QUESTIONS[current_category][current_question_index]

    # Envoi de la réponse
    data = get_text_message_input(wa_id, response)
    send_message(data)

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
