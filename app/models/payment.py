from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel

class Payment(BaseModel):
    ticket_number: str
    amount: float
    payment_type: str
    payment_method: str
    installments: int
    transaction_id: str
    date: date
    status: str = 'pending'  # Default status is 'pending'

class Discrepancy(BaseModel):
    description: str
    difference: float

class ReconciliationResult(BaseModel):
    status: str
    total_expected: float
    total_received: float
    discrepancies: List[Discrepancy] 