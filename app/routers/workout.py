from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from app.services.wger_service import WgerService
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep
from. import api_router, router, templates

wger_service = WgerService()

@router.get("/workouts", response_class=HTMLResponse)
async def workouts_view(request: Request, user: AuthDep, db: SessionDep):
    return templates.TemplateResponse(
        request=request,
        name="workouts.html",
        context={
            "user": user
        }
    )

@api_router.get("/workouts/search")
async def search_exercises(q: str | None = Query(default=None), limit: int = Query(default=50, ge=1, le=50), offset: int = Query(default=0, ge=0)):
    try:
        results = await wger_service.search_exercises(query = q, limit = limit, offset = offset)
        return results
    except Exception:
        raise HTTPException(
            status_code = 500,
            detail = "Could not fetch exercises from wger API"
        )
    
@api_router.get("/workouts/{exercise_id}")
async def get_exercise(exercise_id: int):
    try:
        exercise = await wger_service.get_exercise(exercise_id)
        return exercise
    except Exception:
        raise HTTPException(
            status_code = 404,
            detail = "Exercise not found"
        )
    
def extract_primary_muscle(exercise: dict) -> str:
    muscles = exercise.get("muscles") or []
    if muscles:
        name = muscles[0].get("name")
        if name:
            return name
    secondary = exercise.get("muscles_secondary") or []
    if secondary:
        name = secondary[0].get("name")
        if name:
            return name
    category = exercise.get("category") or {}
    return category.get("name", "") or ""


def extract_equipment(exercise: dict) -> list[str]:
    equipment = exercise.get("equipment") or []
    return [item.get("name") for item in equipment if item.get("name")]


def extract_difficulty(exercise: dict) -> str:
    return exercise.get("difficulty") or ""


def extract_exercise_name(exercise: dict) -> str:
    name = exercise.get("name")
    category_name = (exercise.get("category") or {}).get("name") or ""

    translations = exercise.get("translations") or []
    if isinstance(translations, list):
        english = next((item for item in translations if item.get("language") == 2 and item.get("name") and item.get("name") != category_name), None)
        if english:
            return english.get("name")
        any_translation = next((item for item in translations if item.get("name") and item.get("name") != category_name), None)
        if any_translation:
            return any_translation.get("name")

    nested = exercise.get("exercises") or []
    if isinstance(nested, list):
        english = next((item for item in nested if item.get("language") == 2 and item.get("name") and item.get("name") != category_name), None)
        if english:
            return english.get("name")
        any_nested = next((item for item in nested if item.get("name") and item.get("name") != category_name), None)
        if any_nested:
            return any_nested.get("name")

    if name and name != category_name:
        return name

    return "Unnamed exercise"


@api_router.get("/workouts/{exercise_id}/remix")
async def remix_exercise(exercise_id: int):
    try:
        base_exercise = await wger_service.get_exercise(exercise_id)
        primary_muscle = extract_primary_muscle(base_exercise)
        equipment = extract_equipment(base_exercise)
        difficulty = extract_difficulty(base_exercise)
        base_category = (base_exercise.get("category") or {}).get("name") or ""

        query_parts = []
        if base_category:
            query_parts.append(base_category)
        if primary_muscle and primary_muscle.lower() != base_category.lower():
            query_parts.append(primary_muscle)
        if difficulty:
            query_parts.append(difficulty)
        query = " ".join(query_parts).strip() or base_exercise.get("name") or ""
        api_results = await wger_service.search_exercises(query=query, limit=50)
    except Exception:
        raise HTTPException(
            status_code = 500,
            detail = "Could not fetch remix suggestions"
        )

    suggestions = []
    candidates = []

    for item in api_results.get("results", []):
        if item.get("id") == exercise_id:
            continue

        item_muscles = [m.get("name") for m in (item.get("muscles") or []) if m.get("name")]
        item_muscles += [m.get("name") for m in (item.get("muscles_secondary") or []) if m.get("name")]
        item_equipment = [e.get("name") for e in (item.get("equipment") or []) if e.get("name")]
        item_category = (item.get("category") or {}).get("name") or ""
        item_difficulty = extract_difficulty(item)

        muscle_match = primary_muscle and primary_muscle in item_muscles
        equipment_match = bool(set(equipment) & set(item_equipment))
        category_match = base_category and item_category == base_category
        difficulty_match = difficulty and item_difficulty == difficulty

        score = 0
        if muscle_match:
            score += 50
        if equipment_match:
            score += 15
        if category_match:
            score += 30
        if difficulty_match:
            score += 3

        candidates.append({
            "exercise_api_id": item.get("id"),
            "exercise_name": extract_exercise_name(item),
            "primary_muscle": item_muscles[0] if item_muscles else "Unknown",
            "equipment": item_equipment,
            "category": item_category,
            "difficulty": item_difficulty,
            "score": score,
        })

    if base_category:
        suggestions = [c for c in candidates if c["category"] == base_category]
        if not suggestions:
            suggestions = [c for c in candidates if c["primary_muscle"] == primary_muscle]
    elif primary_muscle:
        suggestions = [c for c in candidates if c["primary_muscle"] == primary_muscle]
    else:
        suggestions = candidates

    if len(suggestions) < 5:
        extra = [c for c in candidates if c not in suggestions]
        suggestions += extra

    suggestions = sorted(suggestions, key=lambda item: item["score"], reverse=True)[:5]

    return {
        "based_on": {
            "id": base_exercise.get("id"),
            "name": base_exercise.get("name"),
            "primary_muscle": primary_muscle,
            "equipment": equipment,
            "difficulty": difficulty,
            "category": base_category,
        },
        "suggestions": suggestions
    }