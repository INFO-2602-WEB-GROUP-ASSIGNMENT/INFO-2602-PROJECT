from fastapi import HTTPException
from app.dependencies import SessionDep, AuthDep
from sqlmodel import select
from app.models import Routine, RoutineExercise
from app.services.wger_service import WgerService
from app.schemas.routine import RoutineCreate, RoutineExerciseCreate, RoutineUpdate, RoutineExerciseRemix
from . import api_router

wger_service = WgerService()


def extract_name(exercise: dict) -> str:
    if exercise.get("name"):
        return exercise["name"]

    translations = exercise.get("translations", [])
    for t in translations:
        if t.get("language") == 2 and t.get("name"):
            return t["name"]

    for t in translations:
        if t.get("name"):
            return t["name"]

    exercises = exercise.get("exercises", [])
    for e in exercises:
        if e.get("language") == 2 and e.get("name"):
            return e["name"]

    for e in exercises:
        if e.get("name"):
            return e["name"]

    return "Unknown Exercise"


@api_router.post("/routines/")
async def create_routine(
    routine_data: RoutineCreate,
    db: SessionDep,
    current_user:AuthDep
):
    existing = db.exec(
        select(Routine).where(
            Routine.user_id == current_user.id,
            Routine.day_of_week == routine_data.day_of_week
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"You already have a routine for {routine_data.day_of_week}."
        )

    routine = Routine(
        name=routine_data.day_of_week, 
        user_id=current_user.id,
        day_of_week=routine_data.day_of_week,
        description=routine_data.description
    )

    db.add(routine)
    db.commit()
    db.refresh(routine)

    for exercise_data in routine_data.exercises:
        try:
            exercise = await wger_service.get_exercise(exercise_data.exercise_id)
        except Exception:
            continue

        routine_exercise = RoutineExercise(
            routine_id=routine.id,
            exercise_api_id=exercise_data.exercise_id,
            exercise_name=extract_name(exercise),
            sets=exercise_data.sets,
            reps=exercise_data.reps
        )
        db.add(routine_exercise)

    db.commit()
    db.refresh(routine)

    return {
        "message": "Routine created successfully",
        "routine_id": routine.id,
        "day_of_week": routine.day_of_week
    }

@api_router.get("/routines/")
def get_all_routines(db: SessionDep, current_user: AuthDep):
    return db.exec(
        select(Routine).where(Routine.user_id == current_user.id)
    ).all()


@api_router.get("/routines/{routine_id}")
def get_routine_detail(routine_id: int, db: SessionDep, current_user: AuthDep):
    routine = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    exercises = db.exec(
        select(RoutineExercise).where(RoutineExercise.routine_id == routine_id)
    ).all()

    return {
        "routine": routine.model_dump(),
        "exercises": [exercise.model_dump() for exercise in exercises]
    }


@api_router.patch("/routines/{routine_id}/exercises/{routine_exercise_id}/remix")
def remix_routine_exercise(
    routine_id: int,
    routine_exercise_id: int,
    remix_data: RoutineExerciseRemix,
    db: SessionDep,
    current_user: AuthDep
):
    routine = db.exec(
        select(Routine).where(Routine.id == routine_id, Routine.user_id == current_user.id)
    ).first()
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    routine_exercise = db.get(RoutineExercise, routine_exercise_id)
    if not routine_exercise or routine_exercise.routine_id != routine_id:
        raise HTTPException(status_code=404, detail="Routine exercise not found")

    routine_exercise.exercise_api_id = remix_data.replacement_exercise_id
    routine_exercise.exercise_name = remix_data.replacement_name
    db.add(routine_exercise)
    db.commit()
    db.refresh(routine_exercise)

    return {
        "message": "Exercise swapped successfully",
        "routine_exercise": routine_exercise.model_dump()
    }

@api_router.post("/routines/{routine_id}/add")
async def add_exercise_to_routine(
    routine_id: int,
    exercise_data: RoutineExerciseCreate,
    db: SessionDep,
    current_user: AuthDep
):
    routine = db.get(Routine, routine_id)

    if not routine or routine.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Routine not found"
        )

    existing = db.exec(
        select(RoutineExercise).where(
            RoutineExercise.routine_id == routine_id,
            RoutineExercise.exercise_api_id == exercise_data.exercise_id
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This exercise is already in the routine."
        )

    try:
        exercise = await wger_service.get_exercise(exercise_data.exercise_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Exercise not found in API"
        )

    routine_exercise = RoutineExercise(
        routine_id=routine.id,
        exercise_api_id=exercise_data.exercise_id,
        exercise_name=extract_name(exercise),
        sets=exercise_data.sets,
        reps=exercise_data.reps
    )

    db.add(routine_exercise)
    db.commit()
    db.refresh(routine_exercise)

    return {
        "message": "Exercise added to routine",
        "exercise": routine_exercise
    }