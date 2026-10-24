
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "ration_transactions_synthetic.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["review_label"]).copy()

# Only use information that could be available during initial transaction review.
# Deliberately exclude rule_flags, scenario_label, transaction_id, challan_number,
# and the target review_label to avoid leakage.
numeric_features = [
    "configured_entitlement_kg",
    "recorded_quantity_kg",
    "beneficiary_confirmed_quantity_kg",
    "recorded_stock_before_kg",
]
categorical_features = [
    "fps_id",
    "commodity",
    "authentication_mode",
]

features = numeric_features + categorical_features
X = df[features].copy()
y = df["review_label"].astype(str)

# Basic chronological/date-derived features.
date_values = pd.to_datetime(df["date"], errors="coerce")
X["day_of_week"] = date_values.dt.dayofweek
X["month"] = date_values.dt.month
numeric_features += ["day_of_week", "month"]
features = numeric_features + categorical_features
X[numeric_features] = X[numeric_features].apply(
    pd.to_numeric, errors="coerce"
)

if y.nunique() < 2 or y.value_counts().min() < 2:
    raise ValueError("Need at least two classes and at least two examples per class.")

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y,
)

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])
categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])
preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=42,
    )),
])

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print("Transaction-review classifier trained.")
print(f"Training rows: {len(X_train)}")
print(f"Testing rows: {len(X_test)}")
print("\nClass distribution in test set:")
print(y_test.value_counts())
print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))
print("Confusion matrix (label order: normal, review):")
print(confusion_matrix(y_test, predictions, labels=["normal", "review"]))

artifact = {
    "model": model,
    "features": features,
    "numeric_features": numeric_features,
    "categorical_features": categorical_features,
    "target": "review_label",
    "label_meaning": {
        "normal": "No review label in the synthetic dataset",
        "review": "Requires human review; not proof of fraud",
    },
    "training_data": "synthetic ration transactions",
}

output_path = MODEL_DIR / "transaction_review_classifier.joblib"
joblib.dump(artifact, output_path)
print(f"\nSaved model: {output_path}")
print("Note: synthetic-data results are not real-world validation.")
