SmartPDS Synthetic Datasets
All six files contain 200 synthetic records for local development/prototyping.

1 ageing_spoilage_dataset.csv - Feature 1; target: risk_level/spoilage_observed.
2 demand_forecasting_dataset.csv - Feature 2; time field: date; target: demand_kg.
3 inventory_copilot_dataset.csv - Feature 3; target: intent.
4 receipt_challan_dataset.csv - Feature 4 ground-truth fields for OCR extraction validation.
   It is NOT an image dataset, so it cannot by itself train an OCR vision model.
5 anomaly_audit_dataset.csv - Feature 5; target: anomaly.
6 multilingual_voice_dataset.csv - Feature 6 intent routing. It is text, not audio; speech-to-text
   requires a separate speech recognition component.

IMPORTANT: All data is synthetic and intended for development/demo purposes only.
Do not present performance on this data as real-world validated performance.
