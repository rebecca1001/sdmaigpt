import os

from dotenv import load_dotenv

load_dotenv(os.getenv("ENV_FILE", ".env"))


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
