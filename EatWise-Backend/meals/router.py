"""Flutter-compatible /api/meals/ endpoints.

Contracts derived from:
  • lib/features/meals/screens/meals_screen.dart     → GET /saved/, DELETE /delete/{id}/
  • lib/features/meals/screens/curated_menu_screen.dart → GET /recommendations/?ids=1,2,3, POST /save/

All responses match the FoodModel.fromJson() expectations in
lib/features/dashboard/models/food_model.dart.
"""
import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core import models
from app.core.database import get_db
from app.core.errors import err_invalid_request, err_not_found
from app.core.visuals import recipe_visual
from app.core.images_map import recipe_image_url


router = APIRouter(prefix="/meals", tags=["Meals (Flutter)"])


def _serialize_saved_meal(m: models.SavedMeal) -> dict:
    emoji, color = recipe_visual(m.recipe_name or "", None, [m.meal_type] if m.meal_type else [])
    img = (m.image_url or "").strip() or recipe_image_url(m.recipe_name or "")
    return {
        "id": m.id,
        "name": m.recipe_name,
        "recipe_name": m.recipe_name,
        "calories": int(m.calories) if m.calories is not None else 0,
        "protein": float(m.protein) if m.protein is not None else 0.0,
        "carbs": float(m.carbs) if m.carbs is not None else 0.0,
        "fat": float(m.fat) if m.fat is not None else 0.0,
        "meal_type": m.meal_type or "",
        "image_url": img,
        "emoji": emoji,
        "color_hex": color,
        "instructions": m.instructions or "",
        "created_at": m.created_at.isoformat(),
    }


def _serialize_recipe_for_flutter(r: models.Recipe, basket_food_ids: set[int]) -> dict:
    """Map an internal Recipe → the shape CuratedMenuScreen expects.

    All nutrition values returned are PER SERVING (so 129g of protein
    showing up for a 420 kcal "single serving" card never happens again).
    Recipe.servings is honoured: a 4-serving recipe divides everything by 4.

    Flutter reads: recipe | name, calories_estimate | calories, protein, carbs,
    fat, image, instructions.
    """
    servings = max(int(r.servings or 1), 1)

    # ----- Aggregate per-serving nutrition from ingredient list ------------
    sum_kcal = sum_protein = sum_carbs = sum_fat = 0.0
    for ri in r.ingredients:
        n = ri.food.nutrition if ri.food else None
        if not n:
            continue
        factor = float(ri.amount) / 100.0  # per 100 g
        sum_kcal    += float(n.kcal      or 0) * factor
        sum_protein += float(n.protein_g or 0) * factor
        sum_carbs   += float(n.carbs_g   or 0) * factor
        sum_fat     += float(n.fat_g     or 0) * factor

    # Convert to per-serving
    kcal_per_serv    = sum_kcal    / servings
    protein_per_serv = sum_protein / servings
    carbs_per_serv   = sum_carbs   / servings
    fat_per_serv     = sum_fat     / servings

    # Sanity-check against the seeded total_kcal: if our computed value is
    # wildly different, fall back to the stored value (still divided by
    # servings) — this protects against incomplete ingredient lists.
    stored_total = float(r.total_kcal or 0)
    if stored_total > 0:
        stored_per_serv = stored_total / servings
        # If we computed less than 60% of the stored value, ingredients are
        # probably incomplete — trust the stored kcal and scale macros up.
        if sum_kcal > 0 and (kcal_per_serv / stored_per_serv) < 0.6:
            scale = stored_per_serv / kcal_per_serv
            kcal_per_serv     = stored_per_serv
            protein_per_serv *= scale
            carbs_per_serv   *= scale
            fat_per_serv     *= scale

    # Steps as readable text
    try:
        steps_list = json.loads(r.steps) if r.steps else []
        instructions = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps_list))
    except json.JSONDecodeError:
        instructions = r.steps or ""

    tags = [t.tag for t in r.tags]
    emoji, color = recipe_visual(r.title_en, r.cuisine, tags)
    img = recipe_image_url(r.title_en)
    return {
        "id": r.id,
        "recipe": r.title_en,
        "name": r.title_en,
        "title_ar": r.title_ar,
        "calories_estimate": int(round(kcal_per_serv)),
        "calories": int(round(kcal_per_serv)),
        "protein": round(protein_per_serv, 1),
        "carbs":   round(carbs_per_serv, 1),
        "fat":     round(fat_per_serv, 1),
        "cuisine": r.cuisine or "",
        "difficulty": r.difficulty or "",
        "prep_time_min": r.prep_time_min or 0,
        "servings": servings,
        "image": img,
        "image_url": img,
        "emoji": emoji,
        "color_hex": color,
        "instructions": instructions,
        "tags": tags,
    }


# ============================================================
# Saved meals
# ============================================================
@router.get("/saved/")
def list_saved_meals(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (db.query(models.SavedMeal)
              .filter(models.SavedMeal.user_id == user.id)
              .order_by(models.SavedMeal.created_at.desc())
              .all())
    return [_serialize_saved_meal(m) for m in rows]


@router.post("/save/", status_code=status.HTTP_201_CREATED)
def save_meal(
    body: dict,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe_name = body.get("recipe_name") or body.get("name") or body.get("recipe")
    if not recipe_name:
        raise err_invalid_request("recipe_name is required")

    def _to_num(v, default=0.0):
        try:
            return float(v) if v is not None else default
        except (TypeError, ValueError):
            return default

    m = models.SavedMeal(
        user_id=user.id,
        recipe_name=str(recipe_name)[:200],
        calories=int(_to_num(body.get("calories") or body.get("calories_estimate"))),
        protein=_to_num(body.get("protein")),
        carbs=_to_num(body.get("carbs")),
        fat=_to_num(body.get("fat")),
        image_url=str(body.get("image_url") or body.get("image") or "")[:500],
        instructions=str(body.get("instructions") or ""),
        meal_type=str(body.get("meal_type") or "")[:30],
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize_saved_meal(m)


@router.delete("/delete/{meal_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_meal(
    meal_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = db.query(models.SavedMeal).filter(
        models.SavedMeal.id == meal_id,
        models.SavedMeal.user_id == user.id,
    ).first()
    if not m:
        raise err_not_found("Meal not found")
    db.delete(m)
    db.commit()
    return None


# ============================================================
# Recommendation engine — goal + health condition + allergies aware
# ============================================================

# Allergen → keyword map (matches Flutter's PROFILE options)
_ALLERGY_KEYWORDS = {
    "dairy":      ["milk", "yogurt", "cheese", "laban", "labneh"],
    "peanuts":    ["peanut"],
    "gluten":     ["bread", "wheat", "flour", "pasta", "oats", "barley"],
    "shellfish":  ["shrimp", "prawn", "crab", "lobster", "oyster"],
    "soy":        ["soy", "soya", "tofu"],
    "eggs":       ["egg"],
    "tree nuts":  ["almond", "walnut", "cashew", "pistachio", "hazelnut"],
    "sesame":     ["sesame", "tahini"],
    "fish":       ["salmon", "tuna", "fish"],
}


def _aggregate_recipe_nutrition(recipe: models.Recipe) -> dict:
    """Sum nutrition across all ingredients, scaled by per-ingredient amount."""
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0,
              "fat": 0.0, "sugar": 0.0, "fiber": 0.0, "sodium": 0.0}
    for ri in recipe.ingredients:
        n = ri.food.nutrition if ri.food else None
        if not n:
            continue
        # NutritionFact is per 100 g; recipe ingredient amount is in grams.
        factor = float(ri.amount) / 100.0
        totals["kcal"]    += float(n.kcal or 0)       * factor
        totals["protein"] += float(n.protein_g or 0)  * factor
        totals["carbs"]   += float(n.carbs_g or 0)    * factor
        totals["fat"]     += float(n.fat_g or 0)      * factor
        totals["sugar"]   += float(n.sugar_g or 0)    * factor
        totals["fiber"]   += float(n.fiber_g or 0)    * factor
        totals["sodium"]  += float(n.sodium_mg or 0)  * factor
    # Per-serving (recipe.servings, default 1)
    servings = max(int(recipe.servings or 1), 1)
    for k in totals:
        totals[k] = totals[k] / servings
    return totals


def _goal_fit(goal: str | None, kcal: float, protein: float, fiber: float) -> tuple[float, str]:
    """Smooth scoring 0..1 of how well a recipe fits the user's health goal.

    Returns (score, reason_text).
    """
    g = (goal or "").strip().lower()

    # --- Weight loss: prefer lower kcal, more fiber ---
    if "loss" in g or "lose" in g:
        if   kcal <= 350: base = 1.00
        elif kcal <= 500: base = 0.85
        elif kcal <= 650: base = 0.55
        else:             base = 0.20
        # Reward fiber (satiety)
        if fiber >= 6:    base = min(1.0, base + 0.08)
        return base, f"Fits weight-loss goal ({int(kcal)} kcal)"

    # --- Muscle gain: prefer higher kcal AND high protein ---
    if "muscle" in g or "gain" in g or "bulk" in g:
        if   kcal >= 650: base = 1.00
        elif kcal >= 500: base = 0.85
        elif kcal >= 400: base = 0.55
        else:             base = 0.20
        # Reward protein density
        if protein >= 30: base = min(1.0, base + 0.10)
        elif protein >= 20: base = min(1.0, base + 0.05)
        return base, f"Fits muscle-gain goal ({int(kcal)} kcal, {protein:.0f} g protein)"

    # --- Maintain: prefer balanced 400–650 kcal ---
    if "maintain" in g:
        if 400 <= kcal <= 650:    return 1.00, f"Balanced for maintenance ({int(kcal)} kcal)"
        if 300 <= kcal <= 750:    return 0.80, f"Close to maintenance range"
        return 0.50, f"Outside ideal maintenance range"

    # No goal set — neutral score
    return 0.70, ""


def _condition_check(condition: str | None, totals: dict) -> tuple[bool, float, str | None]:
    """Apply health-condition rules to (a) hard-block unsafe recipes and
    (b) soft-rank borderline ones.

    Returns (is_safe, score_modifier, warning_or_reason).
    """
    c = (condition or "None").strip().lower()
    if not c or c == "none":
        return True, 1.0, None

    sugar  = totals["sugar"]
    sodium = totals["sodium"]
    fat    = totals["fat"]
    fiber  = totals["fiber"]
    carbs  = totals["carbs"]

    if "diabet" in c or "سكر" in c:
        # Hard block: very-high sugar
        if sugar > 30:
            return False, 0.0, f"Too much sugar for diabetes ({sugar:.0f} g)"
        # Soft penalty band
        if sugar > 15:
            return True, 0.55, f"Elevated sugar ({sugar:.0f} g) — eat in moderation"
        # Bonus for high-fiber low-sugar
        if fiber >= 5 and sugar <= 8:
            return True, 1.10, f"Diabetes-friendly (fiber {fiber:.0f} g, sugar {sugar:.0f} g)"
        return True, 1.0, None

    if "blood pressure" in c or "hypertension" in c or "ضغط" in c:
        if sodium > 1500:
            return False, 0.0, f"Too much sodium for blood pressure ({sodium:.0f} mg)"
        if sodium > 800:
            return True, 0.55, f"Elevated sodium ({sodium:.0f} mg) — eat sparingly"
        if sodium <= 300:
            return True, 1.10, f"Low-sodium choice ({sodium:.0f} mg)"
        return True, 1.0, None

    if "heart" in c or "cardio" in c or "قلب" in c:
        if fat > 35:
            return False, 0.0, f"Too much fat for heart health ({fat:.0f} g)"
        if fat > 25:
            return True, 0.6, f"Elevated fat ({fat:.0f} g)"
        if fat <= 12 and fiber >= 4:
            return True, 1.10, f"Heart-healthy (low fat, fiber-rich)"
        return True, 1.0, None

    if "kidney" in c or "ckd" in c or "كلى" in c:
        if sodium > 1000:
            return False, 0.0, f"Too much sodium for kidney health"
        if totals["protein"] > 40:
            return True, 0.7, f"High protein — discuss portion with your doctor"
        return True, 1.0, None

    return True, 1.0, None


def _allergy_block(recipe: models.Recipe, blocked_keywords: set[str]) -> str | None:
    """Return the first allergen keyword found in this recipe, or None."""
    if not blocked_keywords:
        return None
    for ri in recipe.ingredients:
        if not ri.food:
            continue
        nm = (ri.food.name_en or "").lower()
        for kw in blocked_keywords:
            if kw in nm:
                return kw
    return None


@router.get("/recommendations/")
def meal_recommendations(
    ids: str = Query("", description="Comma-separated product IDs, e.g. '1,4,7'"),
    limit: int = Query(6, ge=1, le=20),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recipe suggestions ranked by:

      1. Allergy safety (hard filter — never suggest unsafe recipes)
      2. Health-condition safety (hard filter for serious thresholds,
         soft penalty for borderline values)
      3. Ingredient overlap with the user's basket / pantry
      4. Goal fit (weight loss / muscle gain / maintain)

    The scored list also returns a `reason` field per recipe so the UI
    can show "Why this recipe?".
    """
    # ---- Parse basket IDs --------------------------------------------------
    try:
        basket_food_ids = {int(x) for x in ids.split(",") if x.strip().isdigit()}
    except ValueError:
        basket_food_ids = set()

    # ---- Load profile (allergies + goal + condition) -----------------------
    ap = db.query(models.AccountProfile).filter(
        models.AccountProfile.user_id == user.id
    ).first()
    allergy_list: list[str] = []
    if ap and ap.allergies and ap.allergies.lower() != "none":
        allergy_list = [a.strip().lower() for a in ap.allergies.split(",") if a.strip()]
    blocked_keywords: set[str] = set()
    for a in allergy_list:
        for ak, kws in _ALLERGY_KEYWORDS.items():
            if ak in a:
                blocked_keywords.update(kws)
    goal = ap.health_goal if ap else None
    condition = ap.health_condition if ap else None

    # ---- Score every active recipe -----------------------------------------
    recipes = db.query(models.Recipe).filter(models.Recipe.is_active == True).all()
    scored: list[tuple[float, models.Recipe, str]] = []
    for r in recipes:
        # 1. Allergy filter — hard block
        hit = _allergy_block(r, blocked_keywords)
        if hit:
            continue  # never recommend unsafe recipes

        # Ingredients overlap with basket
        ing_food_ids = {ri.food.id for ri in r.ingredients if ri.food}
        if not ing_food_ids:
            continue
        covered = len(ing_food_ids & basket_food_ids)
        coverage = covered / len(ing_food_ids) if ing_food_ids else 0
        basket_match_ratio = (covered / len(basket_food_ids)) if basket_food_ids else 0

        # When user picked items, require AT LEAST ONE match — fixes the
        # "I picked apple but got Kabsa" complaint.
        if basket_food_ids and covered == 0:
            continue

        # Aggregate per-serving nutrition
        totals = _aggregate_recipe_nutrition(r)

        # 2. Health-condition check
        is_safe, cond_mod, cond_note = _condition_check(condition, totals)
        if not is_safe:
            continue

        # 3. Goal fit
        goal_score, goal_reason = _goal_fit(
            goal, totals["kcal"], totals["protein"], totals["fiber"]
        )

        # 4. Final score (weighted)
        if basket_food_ids:
            # When user has a basket, ingredients dominate the score
            score = (
                0.50 * coverage
                + 0.20 * basket_match_ratio
                + 0.30 * goal_score
            )
        else:
            score = goal_score
        score *= cond_mod

        # Build reason string for the UI
        reasons = []
        if covered:
            reasons.append(f"uses {covered} of your items")
        if goal_reason:
            reasons.append(goal_reason.lower())
        if cond_note:
            reasons.append(cond_note.lower())
        reason = "; ".join(reasons) if reasons else "balanced choice"

        scored.append((score, r, reason))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:limit]

    out = []
    for score, r, reason in top:
        item = _serialize_recipe_for_flutter(r, basket_food_ids)
        item["reason"] = reason
        item["score"] = round(score, 3)
        out.append(item)

    return {
        "count": len(out),
        "recommended_recipes": out,
        "applied_filters": {
            "goal": goal,
            "condition": condition,
            "allergies": allergy_list,
            "basket_size": len(basket_food_ids),
        },
        "disclaimer": "Not intended for medical purposes. For general wellness only.",
    }
