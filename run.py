import logging
import redis

from app import create_app


app = create_app()

if __name__ == "__main__":
    logging.info("Flask app started")
    redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)
    app.run(host="0.0.0.0", port=8000)
