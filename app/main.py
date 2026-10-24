
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.ageing import assess_ageing_risk
from app.receipt_ocr import router as receipt_ocr_router
app = FastAPI(title="SmartPDS AI Service")
app.include_router(receipt_ocr_router)

# Project and model paths
BASE_DIR = Path(__file__).resolve().parent.parent

INVENTORY_MODEL_PATH = (
    BASE_DIR / "models" / "inventory_intent_model.joblib"
)
MULTILINGUAL_MODEL_PATH = (
    BASE_DIR / "models" / "multilingual_intent_model.joblib"
)

# Load trained models
inventory_model = joblib.load(INVENTORY_MODEL_PATH)
multilingual_model = joblib.load(MULTILINGUAL_MODEL_PATH)


# Request schemas
class BatchInput(BaseModel):
    batch_id: str
    quantity_kg: float = Field(ge=0)
    received_days_ago: int = Field(ge=0)
    days_to_expiry: int | None = None


class InventoryQuery(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class MultilingualQuery(BaseModel):
    query: str = Field(min_length=1, max_length=500)


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# Ageing risk assessment
@app.post("/ageing-risk")
def ageing_risk(batch: BatchInput):
    result = assess_ageing_risk(
        batch.received_days_ago,
        batch.days_to_expiry
    )

    return {
        "batch_id": batch.batch_id,
        "quantity_kg": batch.quantity_kg,
        **result,
        "assessment_type": "rule_based_prototype"
    }


# Existing inventory copilot
@app.post("/inventory-copilot")
def inventory_copilot(request: InventoryQuery):
    query = request.query.strip()
    intent = inventory_model.predict([query])[0]

    return {
        "query": query,
        "predicted_intent": intent,
        "status": "intent_classified",
        "data_available": False,
        "message": (
            "Question classified successfully. "
            "Connect an inventory data source to retrieve actual stock information."
        )
    }


# Hindi and English text assistant
@app.post("/multilingual-assistant")
def multilingual_assistant(request: MultilingualQuery):
    query = request.query.strip()
    intent = multilingual_model.predict([query])[0]

    return {
        "query": query,
        "predicted_intent": intent,
        "status": "intent_classified",
        "data_available": False,
        "message": (
            "Query classified successfully. "
            "Connect the relevant data source to retrieve actual information."
        )
    }
