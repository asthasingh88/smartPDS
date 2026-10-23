
from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "inventory_intent_model.joblib"

model = joblib.load(MODEL_PATH)

test_queries = [
    "How much rice is in stock?",
    "Show today's wheat dispatch",
    "Which batch expires first?",
    "How much stock came in this week?",
    "Which commodities have low stock?",
]

for query in test_queries:
    intent = model.predict([query])[0]
    print(f"Question: {query}")
    print(f"Predicted intent: {intent}")
    print("-" * 40)
