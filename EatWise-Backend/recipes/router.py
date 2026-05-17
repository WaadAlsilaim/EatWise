"""Recipes & foods catalogue router."""
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core import models
from app.core.database import get_db
from app.core.errors import err_not_found
from app.core.responses import ok


router = APIRouter(tags=["Recipes"])


@router.get("/foods")
def list_foods(
    q: str | None = Query(None, min_length=1, max_length=80),
    category: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.FoodItem).filter(models.FoodItem.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.FoodItem.name_ar.ilike(like),
            models.FoodItem.name_en.ilike(like),
        ))
    if category:
        query = query.filter(models.FoodItem.category == category)
    rows = query.limit(limit).all()

    def serialize(f: models.FoodItem):
        n = f.nutrition
        return {
            "id": f.id, "name_ar": f.name_ar, "name_en": f.name_en,
            "category": f.category, "brand": f.brand, "unit": f.unit,
            "nutrition": None if not n else {
                "kcal": float(n.kcal), "protein_g": float(n.protein_g),
                "carbs_g": float(n.carbs_g), "fat_g": float(n.fat_g),
                "sugar_g": float(n.sugar_g or 0), "fiber_g": float(n.fiber_g or 0),
                "sodium_mg": float(n.sodium_mg or 0),
                "per_amount": float(n.per_amount), "per_unit": n.per_unit,
            }
        }

    return ok([serialize(f) for f in rows])


@router.get("/foods/{food_id}")
def get_food(food_id: int, db: Session = Depends(get_db)):
    f = db.query(models.FoodItem).filter(models.FoodItem.id == food_id).first()
    if not f:
        raise err_not_found("Food not found")
    n = f.nutrition
    return ok({
        "id": f.id, "name_ar": f.name_ar, "name_en": f.name_en,
        "category": f.category, "brand": f.brand, "unit": f.unit,
        "nutrition": None if not n else {
            "kcal": float(n.kcal), "protein_g": float(n.protein_g),
            "carbs_g": float(n.carbs_g), "fat_g": float(n.fat_g),
            "sugar_g": float(n.sugar_g or 0), "fiber_g": float(n.fiber_g or 0),
            "sodium_mg": float(n.sodium_mg or 0),
            "per_amount": float(n.per_amount), "per_unit": n.per_unit,
        }
    })


@router.get("/recipes")
def list_recipes(
    q: str | None = None,
    cuisine: str | None = None,
    max_kcal: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Recipe).filter(models.Recipe.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            models.Recipe.title_ar.ilike(like),
            models.Recipe.title_en.ilike(like),
        ))
    if cuisine:
        query = query.filter(models.Recipe.cuisine == cuisine)
    if max_kcal:
        query = query.filter(models.Recipe.total_kcal <= max_kcal)
    rows = query.limit(limit).all()
    return ok([{
        "id": r.id, "title_ar": r.title_ar, "title_en": r.title_en,
        "cuisine": r.cuisine, "difficulty": r.difficulty,
        "prep_time_min": r.prep_time_min, "servings": r.servings,
        "total_kcal": float(r.total_kcal) if r.total_kcal else None,
        "tags": [t.tag for t in r.tags],
    } for r in rows])


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not r:
        raise err_not_found("Recipe not found")
    try:
        steps = json.loads(r.steps) if r.steps else []
    except json.JSONDecodeError:
        steps = [r.steps]

    ingredients = []
    for ri in r.ingredients:
        f = ri.food
        ingredients.append({
            "food_id": f.id, "name_ar": f.name_ar, "name_en": f.name_en,
            "amount": float(ri.amount), "unit": ri.unit,
            "optional": ri.optional,
        })
    return ok({
        "id": r.id, "title_ar": r.title_ar, "title_en": r.title_en,
        "description": r.description, "steps": steps,
        "cuisine": r.cuisine, "difficulty": r.difficulty,
        "prep_time_min": r.prep_time_min, "servings": r.servings,
        "total_kcal": float(r.total_kcal) if r.total_kcal else None,
        "ingredients": ingredients,
        "tags": [t.tag for t in r.tags],
    })
