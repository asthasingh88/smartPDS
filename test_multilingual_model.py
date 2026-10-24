
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "multilingual_intent_model.joblib"

model = joblib.load(MODEL_PATH)

queries = [
    "Aaj kitna ration dispatch hua?",
    "Godown mein kitna chawal bacha hai?",
    "Kaunsa batch pehle expire hoga?",
    "Is mahine ki demand kitni hai?",
    "Kya stock mein koi gadbad hai?",
    "Show today's dispatch",
    "How much rice is left?",
    "Which batch expires first?",
    "Forecast next month's demand",
    "Check for stock mismatch",
]

for query in queries:
    intent = model.predict([query])[0]
    print(f"Query: {query}")
    print(f"Predicted intent: {intent}")
    print("-" * 45)
