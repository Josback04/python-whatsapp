import mysql.connector
from config import DB_CONFIG

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def ensure_user_exists(user_id):
    """ Vérifie si l'utilisateur existe, sinon l'insère """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()

    cursor.close()
    conn.close()

def get_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT question, answer FROM responses where user_id = %s", (user_id,))
    user_data = cursor.fetchall()

    conn.close()
    return user_data 




def save_answer(user_id, question, answer):
    ensure_user_exists(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()

      # Vérifier si l'utilisateur existe, sinon l'insérer
    
    cursor.execute("INSERT INTO responses (user_id, question, answer) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE answer=%s",
                   (user_id, question, answer, answer))
    
    conn.commit()
    cursor.close()
    conn.close()
