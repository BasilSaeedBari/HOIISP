import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "replace-with-random-string-for-dev")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./app.db")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
HOIISP_BASE_URL = os.getenv("HOIISP_BASE_URL", "http://127.0.0.1:8000")

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
DIGEST_RECIPIENTS = os.getenv("DIGEST_RECIPIENTS", "").split(",")
DIGEST_SEND_DAY = os.getenv("DIGEST_SEND_DAY", "friday")
DIGEST_SEND_TIME = os.getenv("DIGEST_SEND_TIME", "08:00")
