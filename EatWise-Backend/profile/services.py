"""Profile helpers (BMR + daily kcal)."""
from datetime import date


def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Basal Metabolic Rate."""
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


ACTIVITY_FACTOR = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_OFFSET = {
    "cutting": -500,
    "bulking": +300,
    "maintain": 0,
    "health": 0,
}


def compute_daily_kcal(hp) -> int | None:
    """Return estimated daily kcal target given a HealthProfile row."""
    if not (hp.weight_kg and hp.height_cm and hp.date_of_birth and hp.gender and hp.activity_level):
        return None
    today = date.today()
    dob = hp.date_of_birth.date() if hasattr(hp.date_of_birth, "date") else hp.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 10 or age > 100:
        return None
    bmr = mifflin_st_jeor(float(hp.weight_kg), float(hp.height_cm), age, hp.gender)
    tdee = bmr * ACTIVITY_FACTOR.get(hp.activity_level, 1.2)
    tdee += GOAL_OFFSET.get(hp.goal or "maintain", 0)
    return int(max(1000, tdee))
