"""Recommendations router — hybrid recommender (content-based + rules + re-ranking)."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core import models
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_not_found
from app.core.responses import ok


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def _recipe_score(recipe: models.Recipe, basket_foods: set[int],
                  user_allergen_slugs: set[str], goal: str | None,
                  kcal_budget: int | None) -> tuple[float, dict]:
    """Return (score, explanation). Hard-filters reduce score to -1 so caller drops it."""
    has_allergens: List[str] = []
    ingredient_food_ids = set()
    for ri in recipe.ingredients:
        ingredient_food_ids.add(ri.food.id)
        name_en = (ri.food.name_en or "").lower()
        if "milk" in name_en or "yogurt" in name_en or "cheese" in name_en:
            if "lactose" in user_allergen_slugs or "milk" in user_allergen_slugs:
                has_allergens.append("milk/lactose")
        if "wheat" in name_en or "bread" in name_en or "flour" in name_en:
            if "gluten" in user_allergen_slugs:
                has_allergens.append("gluten")
        if "peanut" in name_en:
            if "peanut" in user_allergen_slugs:
                has_allergens.append("peanut")

    if has_allergens:
        return -1.0, {"rejected": "allergen", "details": list(set(has_allergens))}

    # Ingredient coverage: how many ingredients are in the basket
    total = len(ingredient_food_ids) or 1
    covered = len(ingredient_food_ids & basket_foods)
    coverage = covered / total

    # Goal fit
    goal_fit = 0.5
    kcal = float(recipe.total_kcal or 500)
    if goal == "cutting" and kcal <= 500:
        goal_fit = 1.0
    elif goal == "bulking" and kcal >= 600:
        goal_fit = 1.0
    elif goal in ("maintain", "health"):
        goal_fit = 0.7

    # Kcal budget filter
    if kcal_budget and kcal > kcal_budget:
        return -1.0, {"rejected": "kcal_budget"}

    score = 0.2 * coverage + 0.3 * goal_fit + 0.5 * (0.5 + 0.5 * coverage)
    score = round(min(1.0, score), 4)

    return score, {
        "coverage": round(coverage, 3),
        "goal_fit": round(goal_fit, 3),
        "has_allergens": [],
        "missing_ingredients": sorted(ingredient_food_ids - basket_foods)[:10],
    }


@router.post("")
def generate_recommendations(
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    basket_id = body.get("basket_id")
    count = int(body.get("count", 5))
    if not basket_id:
        raise err_invalid_request("basket_id is required")

    basket = db.query(models.Basket).filter(
        models.Basket.id == basket_id,
        models.Basket.user_id == user.id,
    ).first()
    if not basket:
        raise err_not_found("Basket not found")

    basket_foods = {it.food.id for it in basket.items if it.food}
    allergen_slugs = {ua.allergen.slug for ua in user.allergens}
    goal = user.health_profile.goal if user.health_profile else None
    kcal_budget = user.health_profile.daily_kcal if user.health_profile else None

    # Candidate set — all active recipes
    recipes = db.query(models.Recipe).filter(models.Recipe.is_active == True).all()

    scored = []
    for r in recipes:
        score, explain = _recipe_score(r, basket_foods, allergen_slugs, goal, kcal_budget)
        if score < 0:
            continue
        scored.append((score, r, explain))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:count]

    return ok({
        "basket_id": basket.id,
        "goal": goal,
        "kcal_budget": kcal_budget,
        "recipes": [
            {
                "rank": idx + 1,
                "score": score,
                "explain": explain,
                "recipe": {
                    "id": r.id, "title_ar": r.title_ar, "title_en": r.title_en,
                    "cuisine": r.cuisine, "difficulty": r.difficulty,
                    "prep_time_min": r.prep_time_min, "servings": r.servings,
                    "total_kcal": float(r.total_kcal) if r.total_kcal else None,
                    "tags": [t.tag for t in r.tags],
                },
            }
            for idx, (score, r, explain) in enumerate(top)
        ],
        "disclaimer": "Not intended for medical purposes. For general wellness only.",
    })
