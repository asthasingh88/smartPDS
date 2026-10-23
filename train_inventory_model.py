
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "Datasets" / "inventory_copilot_dataset.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "inventory_intent_model.joblib"

# Load dataset
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["query", "intent"])
df["query"] = df["query"].astype(str).str.strip()
df = df[df["query"] != ""]

if df["intent"].nunique() < 2:
    raise ValueError("Training ke liye kam se kam 2 intent classes chahiye.")

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    df["query"],
    df["intent"],
    test_size=0.2,
    random_state=42,
    stratify=df["intent"],
)

# Create and train the ML pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
    ("classifier", LogisticRegression(max_iter=1000)),
])

model.fit(X_train, y_train)

# Evaluate on held-out test data
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"Training examples: {len(X_train)}")
print(f"Testing examples: {len(X_test)}")
print(f"Test accuracy: {accuracy:.2%}")
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

# Save trained model
MODEL_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"\nModel saved to: {MODEL_PATH}")
