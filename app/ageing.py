
def assess_ageing_risk(received_days_ago, days_to_expiry=None):
    if received_days_ago < 0:
        raise ValueError("Batch age cannot be negative")

    if days_to_expiry is not None and days_to_expiry < 0:
        return {
            "risk_level": "red",
            "reason": "Recorded expiry date has passed"
        }

    if days_to_expiry is not None and days_to_expiry <= 7:
        return {
            "risk_level": "red",
            "reason": "Batch is within 7 days of expiry"
        }

    if received_days_ago >= 90:
        return {
            "risk_level": "amber",
            "reason": "Batch has been stored for 90 days or more"
        }

    return {
        "risk_level": "green",
        "reason": "No age-based warning from current rules"
    }
