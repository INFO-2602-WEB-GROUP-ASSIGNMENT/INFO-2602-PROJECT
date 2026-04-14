from typing import Any, Optional, cast

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import SQLModel, select
from sqlalchemy.exc import IntegrityError

from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.models import ProgressLog, Routine, RoutineExercise, User, Workout, WorkoutRoutine
from . import router, templates


class UserRoleUpdate(SQLModel):
    role: str


class RoutineAdminUpdate(SQLModel):
    day_of_week: Optional[str] = None
    description: Optional[str] = None


VALID_USER_ROLES = {"admin", "user"}
VALID_DAYS_OF_WEEK = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def normalize_day_of_week(value: str) -> Optional[str]:
    normalized = value.strip().lower()
    for day in VALID_DAYS_OF_WEEK:
        if day.lower() == normalized:
            return day
    return None


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }


def serialize_routine(routine: Routine) -> dict:
    return {
        "id": routine.id,
        "name": routine.name,
        "user_id": routine.user_id,
        "day_of_week": routine.day_of_week,
        "description": routine.description,
    }


@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep
):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user
        }
    )


@router.get("/api/admin/users")
def list_admin_users(db: SessionDep, current_user: AdminDep):
    users = db.exec(select(User).order_by(cast(Any, User.id))).all()
    return [serialize_user(user) for user in users]


@router.get("/api/admin/users/{user_id}/routines")
def list_user_routines(user_id: int, db: SessionDep, current_user: AdminDep):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    routines = db.exec(
        select(Routine).where(Routine.user_id == user_id).order_by(cast(Any, Routine.id))
    ).all()
    return [serialize_routine(routine) for routine in routines]


@router.patch("/api/admin/users/{user_id}")
def update_admin_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: SessionDep,
    current_user: AdminDep,
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot modify your own account from this page.")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    normalized_role = payload.role.strip().lower()
    if normalized_role not in VALID_USER_ROLES:
        raise HTTPException(status_code=422, detail="Role must be either 'admin' or 'user'.")

    user.role = normalized_role
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.delete("/api/admin/users/{user_id}")
def delete_admin_user(user_id: int, db: SessionDep, current_user: AdminDep):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account from this page.")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    routine_ids = [routine.id for routine in db.exec(select(Routine).where(Routine.user_id == user_id)).all()]
    workout_ids = [workout.id for workout in db.exec(select(Workout).where(Workout.user_id == user_id)).all()]

    if routine_ids:
        for routine_id in routine_ids:
            routine_exercises = db.exec(select(RoutineExercise).where(RoutineExercise.routine_id == routine_id)).all()
            progress_logs = db.exec(select(ProgressLog).where(ProgressLog.routine_id == routine_id)).all()
            workout_links = db.exec(select(WorkoutRoutine).where(WorkoutRoutine.routine_id == routine_id)).all()

            for routine_exercise in routine_exercises:
                db.delete(routine_exercise)

            for progress_log in progress_logs:
                db.delete(progress_log)

            for workout_link in workout_links:
                db.delete(workout_link)

            routine = db.get(Routine, routine_id)
            if routine:
                db.delete(routine)

    if workout_ids:
        for workout_id in workout_ids:
            workout_links = db.exec(select(WorkoutRoutine).where(WorkoutRoutine.workout_id == workout_id)).all()
            for workout_link in workout_links:
                db.delete(workout_link)

            workout = db.get(Workout, workout_id)
            if workout:
                db.delete(workout)

    progress_logs = db.exec(select(ProgressLog).where(ProgressLog.user_id == user_id)).all()
    for progress_log in progress_logs:
        db.delete(progress_log)
    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@router.patch("/api/admin/routines/{routine_id}")
def update_admin_routine(
    routine_id: int,
    payload: RoutineAdminUpdate,
    db: SessionDep,
    current_user: AdminDep,
):
    routine = db.get(Routine, routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    if payload.day_of_week is None and payload.description is None:
        raise HTTPException(status_code=400, detail="No routine changes were provided.")

    if payload.day_of_week is not None:
        normalized_day = normalize_day_of_week(payload.day_of_week)
        if not normalized_day:
            raise HTTPException(
                status_code=422,
                detail=f"day_of_week must be one of: {', '.join(VALID_DAYS_OF_WEEK)}",
            )

        routine.day_of_week = normalized_day
        routine.name = normalized_day

    if payload.description is not None:
        routine.description = payload.description.strip() or None

    db.add(routine)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This user already has a routine for that day.",
        )
    db.refresh(routine)
    return serialize_routine(routine)


@router.delete("/api/admin/routines/{routine_id}")
def delete_admin_routine(routine_id: int, db: SessionDep, current_user: AdminDep):
    routine = db.get(Routine, routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    routine_exercises = db.exec(select(RoutineExercise).where(RoutineExercise.routine_id == routine_id)).all()
    progress_logs = db.exec(select(ProgressLog).where(ProgressLog.routine_id == routine_id)).all()
    workout_links = db.exec(select(WorkoutRoutine).where(WorkoutRoutine.routine_id == routine_id)).all()

    for routine_exercise in routine_exercises:
        db.delete(routine_exercise)

    for progress_log in progress_logs:
        db.delete(progress_log)

    for workout_link in workout_links:
        db.delete(workout_link)

    db.delete(routine)
    db.commit()

    return {"message": "Routine deleted successfully"}
