import mysql.connector # Importer le connecteur
from mysql.connector import Error # Pour la gestion d'erreurs DB
from flask import current_app # Pour accéder à la config (DB credentials)
import datetime # Pour le timestamp created_at
from app.config import logging

def get_db_connection():
    """Établit une connexion à la base de données."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=current_app.config.get("DB_HOST"),
            user=current_app.config.get("DB_USER"),
            password=current_app.config.get("DB_PASSWORD"),
            database=current_app.config.get("DB_NAME")
        )
        logging.debug("Connexion MySQL réussie")
    except Error as e:
        logging.error(f"Erreur de connexion à MySQL: {e}")
    return connection

def ensure_user_exists(wa_id):
    """Vérifie si l'utilisateur existe dans la table 'users', sinon l'ajoute."""
    conn = get_db_connection()
    if not conn:
        return False # Échec de la connexion

    cursor = None
    try:
        cursor = conn.cursor()
        # Utiliser BIGINT pour user_id
        query_select = "SELECT id FROM users WHERE user_id = %s"
        cursor.execute(query_select, (wa_id,)) # wa_id doit être passé comme tuple
        user = cursor.fetchone()

        if user is None:
            # L'utilisateur n'existe pas, l'insérer
            query_insert = """
                INSERT INTO users (user_id, created_at)
                VALUES (%s, %s)
            """
            # Note: username est laissé NULL par défaut si la colonne l'autorise
            current_time = datetime.datetime.now()
            cursor.execute(query_insert, (wa_id, current_time))
            conn.commit()
            logging.info(f"Nouvel utilisateur ajouté à la DB: {wa_id}")
        # else:
            # logging.debug(f"Utilisateur {wa_id} déjà existant.")
        return True

    except Error as e:
        logging.error(f"Erreur DB lors de ensure_user_exists pour {wa_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            logging.debug("Connexion MySQL fermée")

def get_user_data(user_id):
    """Récupère les questions et réponses d'un utilisateur depuis la table 'responses'."""
    conn = get_db_connection()
    if not conn:
        return None  # Indiquer une erreur de connexion

    cursor = None
    user_data = None
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT question, answer FROM responses WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchall()
        if not user_data:
            logging.info(f"Aucune donnée trouvée pour l'utilisateur {user_id}")
        else:
            logging.debug(f"Données récupérées pour l'utilisateur {user_id}")
        return user_data
    except Error as e:
        logging.error(f"Erreur DB lors de la récupération des données pour l'utilisateur {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            logging.debug("Connexion MySQL fermée")

def save_response_to_db(wa_id, question_text, answer_text):
    """Sauvegarde une question et sa réponse dans la table 'responses'."""
    # D'abord, s'assurer que l'utilisateur existe (clé étrangère)
    if not ensure_user_exists(wa_id):
         logging.error(f"Impossible de sauvegarder la réponse car l'utilisateur {wa_id} n'a pas pu être assuré/créé.")
         return False # Arrêter si l'utilisateur ne peut être créé/vérifié

    conn = get_db_connection()
    if not conn:
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO responses (user_id, question, answer, created_at)
            VALUES (%s, %s, %s, %s)
        """
        current_time = datetime.datetime.now()
        # Assurez-vous que wa_id est bien un entier si nécessaire, mais BIGINT accepte de grands nombres.
        # Le connecteur gère souvent bien les types Python -> SQL.
        cursor.execute(query, (wa_id, question_text, answer_text, current_time))
        conn.commit()
        logging.info(f"Réponse sauvegardée en DB pour {wa_id}")
        return True
    except Error as e:
        logging.error(f"Erreur DB lors de save_response_to_db pour {wa_id}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            logging.debug("Connexion MySQL fermée")



