"""CLIP-based zero-shot food classifier.

This module adds a second AI pass on top of YOLO. CLIP (from OpenAI, here
loaded via the `open_clip` package) takes an image plus a list of natural
language descriptions and tells us which one fits best — without any
training. We use it to disambiguate between foods that look similar
(orange vs apple, banana vs date, etc.) where YOLO is weak.

Pipeline used by detector.py:
    1. YOLO runs first  → fast detection, locates items in the image
    2. If YOLO is confident (≥ 0.55) → trust it, skip CLIP
    3. Otherwise run CLIP zero-shot over all foods in the DB
    4. If CLIP's top match scores above CLIP_ACCEPT, use that as the label

The model is ~150 MB. It auto-downloads from HuggingFace on first use
and caches locally; subsequent boots are instant.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core import models


# ---- Model loading (singleton, loaded lazily on first request) ----------
_CLIP_MODEL = None
_CLIP_PREPROCESS = None
_CLIP_TOKENIZER = None
_CLIP_LOAD_ERR: str | None = None
_FOOD_PROMPT_CACHE: dict[int, list[str]] = {}     # food_id → text prompts
_TEXT_FEATURE_CACHE = None                         # cached normalized text features
_TEXT_FEATURE_FOOD_IDS: list[int] = []             # parallel list of food ids


# Public configurable thresholds ------------------------------------------
CLIP_ACCEPT = float(os.getenv("EATWISE_CLIP_ACCEPT", "0.22"))   # min similarity to accept
CLIP_DOMINATE = float(os.getenv("EATWISE_CLIP_DOMINATE", "0.30"))  # above this, CLIP overrides YOLO

# Default model. ViT-B-32 is the best balance of speed/accuracy for CPU.
DEFAULT_MODEL = "ViT-B-32"
DEFAULT_PRETRAINED = "openai"


def is_available() -> bool:
    """Quick check — does NOT trigger a model load."""
    try:
        import open_clip  # noqa: F401
        return True
    except ImportError:
        return False


def _load_model():
    global _CLIP_MODEL, _CLIP_PREPROCESS, _CLIP_TOKENIZER, _CLIP_LOAD_ERR
    if _CLIP_MODEL is not None or _CLIP_LOAD_ERR:
        return _CLIP_MODEL
    try:
        import open_clip  # type: ignore
        model_name   = os.getenv("EATWISE_CLIP_MODEL", DEFAULT_MODEL)
        pretrained   = os.getenv("EATWISE_CLIP_PRETRAINED", DEFAULT_PRETRAINED)
        # The OpenAI ViT-B-32 weights expect quick_gelu activation. Passing
        # the flag explicitly silences the harmless QuickGELU warning and
        # ensures we run the same activation as the pretrained checkpoint.
        kwargs = {"pretrained": pretrained}
        if pretrained == "openai":
            kwargs["force_quick_gelu"] = True
        _CLIP_MODEL, _, _CLIP_PREPROCESS = open_clip.create_model_and_transforms(
            model_name, **kwargs
        )
        _CLIP_MODEL.eval()
        _CLIP_TOKENIZER = open_clip.get_tokenizer(model_name)
        return _CLIP_MODEL
    except Exception as e:
        _CLIP_LOAD_ERR = str(e)
        return None


# ---- Building prompts ---------------------------------------------------

# Generic templates that improve zero-shot accuracy (CLIP works better with
# multiple paraphrased prompts than with a single one).
_PROMPT_TEMPLATES = [
    "a photo of {food}",
    "a close-up photo of {food}",
    "a fresh {food}",
    "{food} on a plate",
    "{food} on a white background",
]


def _prompts_for_food(food: models.FoodItem) -> list[str]:
    """Return a list of natural-language prompts for one food item."""
    if food.id in _FOOD_PROMPT_CACHE:
        return _FOOD_PROMPT_CACHE[food.id]

    name_en = (food.name_en or "").strip().lower()
    if not name_en:
        return []

    # Base name + common alternative names
    aliases = [name_en]
    # Add a friendlier variant for some specific items
    friendlier = {
        "sukari dates":      ["dates", "saudi dates", "khalas dates", "tamr"],
        "almarai full-fat milk":  ["a glass of milk", "fresh milk"],
        "almarai low-fat milk":   ["a glass of milk", "skim milk"],
        "al rabie laban":    ["laban", "buttermilk"],
        "dani yogurt":       ["yogurt"],
        "white cheese":      ["white cheese", "feta cheese"],
        "white bread":       ["white bread", "toast"],
        "brown bread":       ["whole wheat bread", "brown bread"],
        "basmati rice":      ["white rice", "basmati"],
        "chicken breast":    ["raw chicken breast", "grilled chicken"],
        "canned tuna":       ["canned tuna fish"],
        "canned fava beans": ["fava beans", "ful medames"],
        "olive oil":         ["bottle of olive oil"],
        "potato chips":      ["potato chips", "crisps"],
        "orange juice":      ["a glass of orange juice"],
        "mineral water":     ["bottle of water"],
    }
    aliases.extend(friendlier.get(name_en, []))

    prompts: list[str] = []
    for alias in aliases:
        for tpl in _PROMPT_TEMPLATES:
            prompts.append(tpl.format(food=alias))

    _FOOD_PROMPT_CACHE[food.id] = prompts
    return prompts


def _build_text_features(db: Session) -> bool:
    """Pre-encode every food in the DB once. Cached for the lifetime
    of the process — refreshes only when the food set changes (rare)."""
    global _TEXT_FEATURE_CACHE, _TEXT_FEATURE_FOOD_IDS
    if _TEXT_FEATURE_CACHE is not None:
        return True

    model = _load_model()
    if model is None:
        return False

    foods = db.query(models.FoodItem).all()
    if not foods:
        return False

    try:
        import torch  # type: ignore
        all_prompts: list[str] = []
        prompt_owner: list[int] = []  # which food each prompt belongs to
        for f in foods:
            ps = _prompts_for_food(f)
            for p in ps:
                all_prompts.append(p)
                prompt_owner.append(f.id)

        if not all_prompts:
            return False

        with torch.no_grad():
            tokens = _CLIP_TOKENIZER(all_prompts)
            text_features = model.encode_text(tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)

        # Average prompt features per food
        unique_ids: list[int] = []
        avg_features = []
        for f in foods:
            mask = [i for i, owner in enumerate(prompt_owner) if owner == f.id]
            if not mask:
                continue
            feat = text_features[mask].mean(dim=0)
            feat = feat / feat.norm()
            avg_features.append(feat)
            unique_ids.append(f.id)

        _TEXT_FEATURE_CACHE = torch.stack(avg_features)
        _TEXT_FEATURE_FOOD_IDS = unique_ids
        return True
    except Exception as e:
        global _CLIP_LOAD_ERR
        _CLIP_LOAD_ERR = f"text-features build failed: {e}"
        return False


# ---- Public API ---------------------------------------------------------

def classify_image(image_path: Path, db: Session,
                   top_k: int = 3) -> list[dict[str, Any]]:
    """Return the top-K most similar foods from the DB for this image.

    Each result is:
      { "food_id": int, "food_name_en": str, "similarity": float (0..1) }

    Empty list if CLIP isn't available or fails.
    """
    if not is_available():
        return []

    model = _load_model()
    if model is None:
        return []

    if not _build_text_features(db):
        return []

    try:
        import torch  # type: ignore
        from PIL import Image  # type: ignore
        with Image.open(image_path) as im:
            im = im.convert("RGB")
            img_tensor = _CLIP_PREPROCESS(im).unsqueeze(0)

        with torch.no_grad():
            img_features = model.encode_image(img_tensor)
            img_features /= img_features.norm(dim=-1, keepdim=True)
            # Cosine similarity to every food
            sims = (img_features @ _TEXT_FEATURE_CACHE.T).squeeze(0)

        # top-k
        k = min(top_k, sims.shape[0])
        topk = torch.topk(sims, k=k)
        out = []
        for score, idx in zip(topk.values.tolist(), topk.indices.tolist()):
            food_id = _TEXT_FEATURE_FOOD_IDS[idx]
            food = db.query(models.FoodItem).filter(models.FoodItem.id == food_id).first()
            if not food:
                continue
            out.append({
                "food_id": food.id,
                "food_name_en": food.name_en,
                "food_name_ar": food.name_ar,
                "category": food.category,
                "similarity": float(score),
            })
        return out
    except Exception:
        return []


def best_match(image_path: Path, db: Session) -> dict[str, Any] | None:
    """Convenience: return the single best CLIP match if it exceeds CLIP_ACCEPT."""
    candidates = classify_image(image_path, db, top_k=1)
    if not candidates:
        return None
    top = candidates[0]
    if top["similarity"] < CLIP_ACCEPT:
        return None
    return top
