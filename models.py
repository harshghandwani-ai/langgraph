from pydantic import BaseModel, Field


class Expense(BaseModel):
    amount: float = Field(..., description="The monetary amount spent")
    category: str = Field(..., description="Category of expense e.g. food, shopping, transport")
    date: str = Field(..., description="Date of expense in YYYY-MM-DD format")
    payment_mode: str = Field(..., description="Payment method e.g. cash, UPI, credit card, debit card")
    description: str = Field(..., description="Brief description of what was purchased")
