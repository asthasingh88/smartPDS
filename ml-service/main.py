
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

app = FastAPI(title="SmartPDS ML API", version="1.0.0")

demand_path = MODEL_DIR / "demand_forecasting.joblib"
review_path = MODEL_DIR / "transaction_review_classifier.joblib"

demand_artifact = joblib.load(demand_path)
review_artifact = joblib.load(review_path)


class DemandRequest(BaseModel):
    commodity: str
    day_of_week: int = Field(ge=0, le=6)
    day_of_month: int = Field(ge=1, le=31)
    day_of_year: int = Field(ge=1, le=366)
    lag_1: float = Field(ge=0)
    lag_7: float = Field(ge=0)
    rolling_mean_7: float = Field(ge=0)


class TransactionRequest(BaseModel):
    configured_entitlement_kg: float = Field(ge=0)
    recorded_quantity_kg: float = Field(ge=0)
    beneficiary_confirmed_quantity_kg: float = Field(ge=0)
    recorded_stock_before_kg: float = Field(ge=0)
    fps_id: str
    commodity: str
    authentication_mode: str
    day_of_week: int = Field(ge=0, le=6)
    month: int = Field(ge=1, le=12)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SmartPDS ML API",
        "models_loaded": True,
        "data_note": "Models trained on synthetic demo datasets",
    }


@app.post("/predict/demand")
def predict_demand(request: DemandRequest):
    try:
        payload = request.model_dump()
        row = pd.DataFrame([payload])[demand_artifact["features"]]
        prediction = float(demand_artifact["model"].predict(row)[0])

        return {
            "commodity": request.commodity,
            "predicted_demand_kg": round(max(0.0, prediction), 2),
            "unit": "kg",
            "model": "demand_forecasting",
            "data_note": "Synthetic-data demo; not a validated real-world forecast",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/predict/transaction-review")
def predict_transaction_review(request: TransactionRequest):
    try:
        payload = request.model_dump()
        row = pd.DataFrame([payload])[review_artifact["features"]]

        model = review_artifact["model"]
        prediction = str(model.predict(row)[0])

        probabilities = model.predict_proba(row)[0]
        classes = list(model.classes_)
        review_probability = (
            float(probabilities[classes.index("review")])
            if "review" in classes else 0.0
        )

        return {
            "review_recommended": prediction == "review",
            "predicted_label": prediction,
            "review_probability": round(review_probability, 4),
            "requires_human_review": prediction == "review",
            "model": "transaction_review_classifier",
            "warning": "Synthetic-data model; this is not proof of fraud",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
