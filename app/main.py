
from pathlib import Path

import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.ageing import assess_ageing_risk

app = FastAPI(title="SmartPDS AI Service")

# Load the trained inventory model
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "inventory_intent_model.joblib"
inventory_model = joblib.load(MODEL_PATH)


class BatchInput(BaseModel):
    batch_id: str
    quantity_kg: float = Field(ge=0)
    received_days_ago: int = Field(ge=0)
    days_to_expiry: int | None = None


class InventoryQuery(BaseModel):
    query: str = Field(min_length=1, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok"}


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
