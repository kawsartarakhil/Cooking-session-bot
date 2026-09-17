import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
DB_NAME = os.getenv("DB_NAME")