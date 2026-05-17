"""SQLAlchemy ORM models — kept in one file for easy navigation."""
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ============================================================
# Users & Authentication
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_hash = Column(String(128), unique=True, nullable=False, index=True)
    phone_enc = Column(String(512), nullable=False)  # encrypted blob (base64)
    display_name = Column(String(80), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    locale = Column(String(8), default="ar", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    health_profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    allergens = relationship("UserAllergen", back_populates="user", cascade="all, delete-orphan")
    conditions = relationship("UserCondition", back_populates="user", cascade="all, delete-orphan")
    baskets = relationship("Basket", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_hash = Column(String(128), nullable=False, index=True)
    code_hash = Column(String(256), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(256), unique=True, nullable=False)
    device_label = Column(String(120), nullable=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")


# ============================================================
# Health profile
# ============================================================
class HealthProfile(Base):
    __tablename__ = "health_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    gender = Column(String(12), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    height_cm = Column(Numeric(5, 2), nullable=True)
    weight_kg = Column(Numeric(5, 2), nullable=True)
    activity_level = Column(String(20), nullable=True)
    goal = Column(String(20), nullable=True)
    daily_kcal = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="health_profile")


class Allergen(Base):
    __tablename__ = "allergens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(40), unique=True, nullable=False)
    name_ar = Column(String(80), nullable=False)
    name_en = Column(String(80), nullable=False)


class UserAllergen(Base):
    __tablename__ = "user_allergens"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    allergen_id = Column(Integer, ForeignKey("allergens.id"), primary_key=True)
    severity = Column(String(12), default="moderate", nullable=False)

    user = relationship("User", back_populates="allergens")
    allergen = relationship("Allergen")


class ChronicCondition(Base):
    __tablename__ = "chronic_conditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(40), unique=True, nullable=False)
    name_ar = Column(String(80), nullable=False)
    name_en = Column(String(80), nullable=False)


class UserCondition(Base):
    __tablename__ = "user_conditions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    condition_id = Column(Integer, ForeignKey("chronic_conditions.id"), primary_key=True)

    user = relationship("User", back_populates="conditions")
    condition = relationship("ChronicCondition")


# ============================================================
# Food catalogue & Recipes
# ============================================================
class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_ar = Column(String(160), nullable=False, index=True)
    name_en = Column(String(160), nullable=False, index=True)
    barcode = Column(String(40), unique=True, nullable=True)
    sfda_id = Column(String(40), nullable=True)
    brand = Column(String(120), nullable=True)
    category = Column(String(60), nullable=True)
    image_path = Column(String(300), nullable=True)
    unit = Column(String(20), default="g", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    nutrition = relationship("NutritionFact", back_populates="food", uselist=False, cascade="all, delete-orphan")


class NutritionFact(Base):
    __tablename__ = "nutrition_facts"

    food_id = Column(Integer, ForeignKey("food_items.id", ondelete="CASCADE"), primary_key=True)
    kcal = Column(Numeric(7, 2), nullable=False, default=0)
    protein_g = Column(Numeric(6, 2), nullable=False, default=0)
    carbs_g = Column(Numeric(6, 2), nullable=False, default=0)
    fat_g = Column(Numeric(6, 2), nullable=False, default=0)
    sugar_g = Column(Numeric(6, 2), default=0)
    fiber_g = Column(Numeric(6, 2), default=0)
    sodium_mg = Column(Numeric(7, 2), default=0)
    per_amount = Column(Numeric(6, 2), default=100, nullable=False)
    per_unit = Column(String(10), default="g", nullable=False)

    food = relationship("FoodItem", back_populates="nutrition")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_ar = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(Text, nullable=False)  # JSON array encoded as string
    cuisine = Column(String(40), nullable=True)
    difficulty = Column(String(12), nullable=True)
    prep_time_min = Column(Integer, nullable=True)
    servings = Column(Integer, default=1, nullable=False)
    total_kcal = Column(Numeric(7, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    tags = relationship("RecipeTag", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    food_id = Column(Integer, ForeignKey("food_items.id"), primary_key=True)
    amount = Column(Numeric(7, 2), nullable=False)
    unit = Column(String(10), nullable=False)
    optional = Column(Boolean, default=False)

    recipe = relationship("Recipe", back_populates="ingredients")
    food = relationship("FoodItem")


class RecipeTag(Base):
    __tablename__ = "recipe_tags"

    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    tag = Column(String(40), primary_key=True)

    recipe = relationship("Recipe", back_populates="tags")


# ============================================================
# Baskets
# ============================================================
class Basket(Base):
    __tablename__ = "baskets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(300), nullable=False)
    status = Column(String(12), default="pending", nullable=False)
    source = Column(String(12), nullable=False)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="baskets")
    items = relationship("BasketItem", back_populates="basket", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_baskets_user_created", "user_id", "created_at"),)


class BasketItem(Base):
    __tablename__ = "basket_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    basket_id = Column(Integer, ForeignKey("baskets.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("food_items.id"), nullable=True)
    raw_label = Column(String(200), nullable=True)
    confidence = Column(Numeric(4, 3), nullable=True)
    quantity = Column(Numeric(7, 2), default=1, nullable=False)
    unit = Column(String(10), default="piece", nullable=False)
    manual = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    basket = relationship("Basket", back_populates="items")
    food = relationship("FoodItem")


# ============================================================
# Alerts & Activity
# ============================================================
class SFDAAlert(Base):
    __tablename__ = "sfda_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sfda_ref = Column(String(80), unique=True, nullable=True)
    title_ar = Column(String(300), nullable=False)
    title_en = Column(String(300), nullable=True)
    alert_type = Column(String(40), nullable=True)
    severity = Column(String(12), nullable=True)
    product_name = Column(String(200), nullable=True)
    source_url = Column(String(400), nullable=True)
    published_at = Column(DateTime, nullable=True)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserAlert(Base):
    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(30), nullable=False)
    sfda_alert_id = Column(Integer, ForeignKey("sfda_alerts.id"), nullable=True)
    basket_id = Column(Integer, ForeignKey("baskets.id"), nullable=True)
    food_id = Column(Integer, ForeignKey("food_items.id"), nullable=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(30), nullable=False)
    amount = Column(Numeric(7, 2), nullable=False)
    unit = Column(String(12), nullable=False)
    kcal_burned = Column(Numeric(7, 2), nullable=True)
    occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(60), nullable=False)
    target = Column(String(120), nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    meta = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# Flutter-compatible Account Profile (matches /api/accounts/me/)
# ============================================================
class AccountProfile(Base):
    """Denormalized profile fields matching exactly what the Flutter app expects.

    Field names mirror the JSON payload the Flutter screens send/read:
    full_name, age, height, weight, health_goal, health_condition, allergies
    (allergies is a comma-separated string like "Dairy, Peanuts, Gluten").
    """
    __tablename__ = "account_profiles"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name = Column(String(120), nullable=True)
    age = Column(Integer, nullable=True)
    height = Column(Numeric(6, 2), nullable=True)          # cm
    weight = Column(Numeric(6, 2), nullable=True)          # kg
    health_goal = Column(String(40), nullable=True)        # "Weight Loss" | "Maintain" | "Muscle Gain"
    health_condition = Column(String(40), nullable=True)   # "None" | "Diabetes" | "Blood Pressure" | "Heart Disease"
    allergies = Column(String(500), nullable=True)         # "Dairy, Peanuts, Gluten" or "None"
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ============================================================
# Saved meals (matches /api/meals/saved/, /save/, /delete/)
# ============================================================
class SavedMeal(Base):
    __tablename__ = "saved_meals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipe_name = Column(String(200), nullable=False)
    calories = Column(Integer, nullable=True)
    protein = Column(Numeric(6, 2), nullable=True)
    carbs = Column(Numeric(6, 2), nullable=True)
    fat = Column(Numeric(6, 2), nullable=True)
    image_url = Column(String(500), nullable=True)
    instructions = Column(Text, nullable=True)
    meal_type = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============================================================
# Pantry — the user's "My Products" personal list.
# Items can be added manually or auto-added from image analysis.
# ============================================================
class PantryItem(Base):
    __tablename__ = "pantry_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("food_items.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(7, 2), default=1, nullable=False)
    unit = Column(String(10), default="piece", nullable=False)
    source = Column(String(20), default="manual", nullable=False)  # 'manual' | 'scan' | 'upload'
    added_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    food = relationship("FoodItem")

    __table_args__ = (
        UniqueConstraint("user_id", "food_id", name="uq_pantry_user_food"),
        Index("idx_pantry_user_added", "user_id", "added_at"),
    )
