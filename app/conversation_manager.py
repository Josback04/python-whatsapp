# # app/conversation_manager.py
# from app.utils.whatsapp_utils import send_message

# def handle_initial_message(wa_id):
#     first_message = """
#     Bonjour ! Que souhaitez-vous faire aujourd'hui ?
#     1. Remplir un formulaire
#     2. Calcul A
#     3. Calcul B
#     4. Calcul C
#     Répondez avec le numéro de votre choix (par exemple "1" pour Formulaire).
#     """
#     send_message(wa_id, first_message)
#     redis_client.hset(wa_id, "current_category", "choix_initial")
