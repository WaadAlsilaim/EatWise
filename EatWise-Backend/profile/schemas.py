"""Profile schemas."""
from datetime import date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


Gender = Literal["male", "female", "other"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
Goal = Literal["cutting", "bulking", "maintain", "health"]
Severity = Literal["mild", "moderate", "severe"]


class HealthIn(BaseModel):
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    height_cm: Optional[float] = Field(None, ge=50, le=250)
    weight_kg: Optional[float] = Field(None, ge=20, le=300)
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None


class HealthOut(HealthIn):
    daily_kcal: Optional[int] = None


class AllergenRef(BaseModel):
    id: int
    slug: str
    name_ar: str
    name_en: str
    severity: Optional[Severity] = None


class ConditionRef(BaseModel):
    id: int
    slug: str
    name_ar: str
    name_en: str


class ProfileOut(BaseModel):
    id: int
    display_name: Optional[str] = None
    locale: str
    phone_masked: str
    health: HealthOut
    allergens: List[AllergenRef]
    conditions: List[ConditionRef]


class ProfileUpdateIn(BaseModel):
    display_name: Optional[str] = Field(None, max_length=80)
    locale: Optional[Literal["ar", "en"]] = None
    health: Optional[HealthIn] = None


class AllergenAddIn(BaseModel):
    allergen_id: int
    severity: Severity = "moderate"


class ConditionAddIn(BaseModel):
    condition_id: int
