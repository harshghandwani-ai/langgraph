import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DB_PATH: str = os.getenv("DB_PATH", "expenses.db")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. Please add it to a .env file or export it as an environment variable."
    )
