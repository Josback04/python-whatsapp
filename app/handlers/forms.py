from app.utils.whatsapp_utils import send_next_question, send_message, get_text_message_input
from config import redis_client

redis_client
def handle_formulaire(wa_id):
    """
    Gère les questions pour le formulaire.
    """
    current_category = "formulaire"
    current_question_index = int(redis_client.hget(wa_id, "current_question_index") or 0)
    questions = [
        "Quel est votre nom ?",
        "Quel est votre âge ?",
        "Quelle est votre profession ?"
    ]

    if current_question_index < len(questions):
        question = questions[current_question_index]
        data = get_text_message_input(wa_id, question)
        send_message(data)
        redis_client.hset(wa_id, "current_question_index", current_question_index + 1)
    else:
        redis_client.hset(wa_id, "current_category", "finished")
        redis_client.hset(wa_id, "current_question_index", 0)
        message = "Merci d'avoir rempli le formulaire."
        data = get_text_message_input(wa_id, message)
        send_message(data)
