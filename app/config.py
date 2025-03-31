import sys
import os
from dotenv import load_dotenv
import logging

import redis




def load_configurations(app):
    load_dotenv()
    app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
    app.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")
    app.config["APP_ID"] = os.getenv("APP_ID")
    app.config["APP_SECRET"] = os.getenv("APP_SECRET")
    app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
    app.config["VERSION"] = os.getenv("VERSION")
    app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
    app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")
    app.config["GEMINI_KEY"] = os.getenv("GEMINI_KEY")

    app.config["DB_HOST"] = os.getenv("DB_HOST")
    app.config["DB_USER"] = os.getenv("DB_USER")
    app.config["DB_PASSWORD"] = os.getenv("DB_PASSWORD")
    app.config["DB_NAME"] = os.getenv("DB_NAME")



PDF_DIR = os.getenv("PDF_DIR")
host=os.getenv("REDIS_HOST")
port=os.getenv("REDIS_PORT")
password= os.getenv("REDIS_PASSWORD")


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

redis_client = redis.StrictRedis(host=host, db=0, password=password, decode_responses=True)
