
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "Datasets" / "multilingual_voice_dataset.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "multilingual_intent_model.joblib"

# Load dataset
df = pd.read_csv(DATA_PATH)

X = df["text"].astype(str)
y = df["intent"]

# Keep training and test examples separate
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Text classification pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), strip_accents=None)),
    ("classifier", LinearSVC())
])

# Train and evaluate
model.fit(X_train, y_train)
predictions = model.predict(X_test)

print("Test accuracy:", round(accuracy_score(y_test, predictions), 3))
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

# Save model separately
MODEL_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)

print(f"\nModel saved to: {MODEL_PATH}")
