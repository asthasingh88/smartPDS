
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_DIR / "dispatch_history_90_days.csv")
df["dispatch_date"] = pd.to_datetime(df["dispatch_date"], errors="coerce")
df["quantity_kg"] = pd.to_numeric(df["quantity_kg"], errors="coerce")
df = df.dropna(subset=["dispatch_date", "quantity_kg", "commodity"])

# Aggregate daily demand by commodity.
daily = (
    df.groupby([df["dispatch_date"].dt.normalize(), "commodity"], as_index=False)
    ["quantity_kg"].sum()
    .rename(columns={"dispatch_date": "date", "quantity_kg": "demand_kg"})
)

daily = daily.sort_values(["commodity", "date"]).reset_index(drop=True)

# Use only information available before the date being predicted.
daily["day_of_week"] = daily["date"].dt.dayofweek
daily["day_of_month"] = daily["date"].dt.day
daily["day_of_year"] = daily["date"].dt.dayofyear

daily["lag_1"] = daily.groupby("commodity")["demand_kg"].shift(1)
daily["lag_7"] = daily.groupby("commodity")["demand_kg"].shift(7)
daily["rolling_mean_7"] = daily.groupby("commodity")["demand_kg"].transform(
    lambda s: s.shift(1).rolling(7, min_periods=3).mean()
)

features = [
    "commodity", "day_of_week", "day_of_month", "day_of_year",
    "lag_1", "lag_7", "rolling_mean_7"
]
daily = daily.dropna(subset=features + ["demand_kg"]).reset_index(drop=True)

if len(daily) < 20:
    raise ValueError(
        f"Only {len(daily)} usable daily rows. "
        "More history is needed for a meaningful time-based evaluation."
    )

# Chronological split: never shuffle time-series rows.
split = int(len(daily) * 0.8)
train = daily.iloc[:split]
test = daily.iloc[split:]

categorical = ["commodity"]
numeric = [c for c in features if c not in categorical]

preprocessor = ColumnTransformer([
    ("commodity", OneHotEncoder(handle_unknown="ignore"), categorical),
    ("numeric", "passthrough", numeric),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(
        n_estimators=200, random_state=42, min_samples_leaf=2
    )),
])

model.fit(train[features], train["demand_kg"])
predictions = model.predict(test[features])

mae = mean_absolute_error(test["demand_kg"], predictions)
rmse = mean_squared_error(test["demand_kg"], predictions) ** 0.5

artifact = {
    "model": model,
    "features": features,
    "target": "demand_kg",
    "training_data": "synthetic dispatch history",
}

joblib.dump(artifact, MODEL_DIR / "demand_forecasting.joblib")

print("Demand forecasting model trained successfully.")
print(f"Training rows: {len(train)}")
print(f"Testing rows: {len(test)}")
print(f"Test MAE: {mae:.2f} kg")
print(f"Test RMSE: {rmse:.2f} kg")
print(f"Saved model: {MODEL_DIR / 'demand_forecasting.joblib'}")
print("Note: These results use synthetic data and are not real-world validation.")
