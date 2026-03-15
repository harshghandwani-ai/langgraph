import json
from datetime import date
from openai import OpenAI
from models import Expense
from config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

TODAY = date.today().isoformat()

SYSTEM_PROMPT = f"""You are an expense extraction assistant.
Today's date is {TODAY}.

From the user's natural language input, extract:
- amount (float): the monetary amount spent
- category (string): one of food, shopping, transport, entertainment, health, utilities, other
- date (string): in YYYY-MM-DD format; use today's date if not specified
- payment_mode (string): e.g. cash, UPI, credit card, debit card; default to "cash" if not mentioned
- description (string): brief noun phrase of what was bought

Respond ONLY with a valid JSON object matching this schema exactly. No explanation, no markdown.
"""


def extract_expense(text: str) -> Expense:
    """Call OpenAI to extract structured expense data from natural language."""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)
    return Expense(**data)
