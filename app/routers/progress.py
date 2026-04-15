from datetime import date, datetime, timedelta
import json

from fastapi import Request, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlmodel import select
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep
from app.models import Routine, RoutineExercise, ProgressLog
from app.schemas.progress import ProgressSaveRequest
from . import router, templates, api_router

DAY_NAME_MAP = {
    "sun": 0, "sunday": 0,
    "mon": 1, "monday": 1,
    "tue": 2, "tues": 2, "tuesday": 2,
    "wed": 3, "wednesday": 3,
    "thu": 4, "thurs": 4, "thursday": 4,
    "fri": 5, "friday": 5,
    "sat": 6, "saturday": 6,
}


def parse_day_index(value: str):
    if not value:
        return None
    token = value.strip().lower()
    if token in DAY_NAME_MAP:
        return DAY_NAME_MAP[token]
    return DAY_NAME_MAP.get(token[:3])


@router.get("/progress", response_class=HTMLResponse)
async def progress_view(request: Request, user: AuthDep, db: SessionDep):
    routines = db.exec(
        select(Routine).where(Routine.user_id == user.id)
    ).all()

    routine_map = {}
    routine_id_to_day = {}

    for routine in routines:
        day_index = parse_day_index(routine.day_of_week)
        if day_index is None:
            day_index = parse_day_index(routine.name)

        if day_index is None:
            continue

        routine_map[day_index] = {
            "id": routine.id,
            "name": routine.name,
            "dayOfWeek": routine.day_of_week,
            "exercises": [],
        }
        routine_id_to_day[routine.id] = day_index

    if routine_id_to_day:
        routine_exercises = db.exec(
            select(RoutineExercise).where(
                RoutineExercise.routine_id.in_(list(routine_id_to_day.keys()))
            )
        ).all()
    else:
        routine_exercises = []

    exercise_by_id = {exercise.id: exercise for exercise in routine_exercises}

    for exercise in routine_exercises:
        day_index = routine_id_to_day.get(exercise.routine_id)
        if day_index is None:
            continue

        if exercise.sets and exercise.reps:
            planned = f"{exercise.sets} × {exercise.reps}"
        elif exercise.sets:
            planned = f"{exercise.sets} sets"
        elif exercise.reps:
            planned = f"{exercise.reps} reps"
        else:
            planned = ""

        routine_map[day_index]["exercises"].append({
            "id": exercise.id,
            "exercise_api_id": exercise.exercise_api_id,
            "name": exercise.exercise_name,
            "planned": planned,
            "sets": exercise.sets or 0,
            "reps": exercise.reps or 0,
        })

    today = date.today()
    year_ago = today - timedelta(days=364)

    saved_logs = db.exec(
        select(ProgressLog).where(
            ProgressLog.user_id == user.id,
            ProgressLog.log_date >= year_ago,
        )
    ).all()

    week_start = today - timedelta(days=(today.weekday() + 1) % 7)

    def parse_minutes(value):
        if not value or not isinstance(value, str):
            return 0
        parts = value.split(":")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]) + int(parts[1]) / 60
        if len(parts) == 1 and parts[0].isdigit():
            return int(parts[0])
        return 0

    def load_entries(logs):
        entries = []
        for log in logs:
            try:
                payload = json.loads(log.payload) if log.payload else {}
            except Exception:
                payload = {}

            entries.append({
                "date": log.log_date.isoformat(),
                "dayIndex": log.day_index,
                "routine_id": log.routine_id,
                "log": payload,
            })
        return entries

    all_progress_entries = load_entries(saved_logs)
    progress_entries = [
        entry for entry in all_progress_entries
        if week_start <= date.fromisoformat(entry["date"]) <= today
    ]

    def get_valid_exercises(entry):
        return [
            v for k, v in entry.get("log", {}).items()
            if not k.startswith("__") and isinstance(v, dict)
        ]

    def build_recent_workouts(entries):
        workouts = []
        for entry in sorted(entries, key=lambda item: item["date"], reverse=True):
            day_idx = entry.get("dayIndex")
            routine = routine_map.get(day_idx, {})
            exercises = get_valid_exercises(entry)
            done = sum(1 for ex in exercises if ex.get("status") == "completed")
            total = len(exercises)

            minutes = 0
            for ex in exercises:
                minutes += parse_minutes(ex.get("time"))

            date_label = entry["date"]
            try:
                log_date = date.fromisoformat(entry["date"])
                if log_date == today:
                    date_label = "Today"
                elif log_date >= today - timedelta(days=6):
                    date_label = log_date.strftime("%a")
                elif log_date >= today - timedelta(days=13):
                    date_label = f"Last {log_date.strftime('%a')}"
                else:
                    date_label = log_date.strftime("%b %d")
            except Exception:
                pass

            workouts.append({
                "name": routine.get("name", "Workout"),
                "date": date_label,
                "dur": f"{minutes} min",
                "done": done,
                "total": total,
            })

        return workouts[:5]

    def build_personal_records(entries):
        records = {}
        for entry in sorted(entries, key=lambda item: item["date"]):
            for key, ex_data in entry.get("log", {}).items():
                if not isinstance(key, str) or key.startswith("__") or not isinstance(ex_data, dict):
                    continue

                try:
                    ex_id = int(key)
                except ValueError:
                    continue

                exercise = exercise_by_id.get(ex_id)
                name = exercise.exercise_name if exercise else f"Exercise {ex_id}"

                max_weight = 0
                for set_data in ex_data.get("sets", []):
                    weight = set_data.get("weight")
                    if isinstance(weight, (int, float)) and weight > max_weight:
                        max_weight = weight

                if max_weight <= 0:
                    continue

                record = records.get(name)
                if record is None or max_weight > record["max"]:
                    change = "+0 lbs"
                    if record is not None:
                        change = f"+{int(max_weight - record['max'])} lbs"

                    records[name] = {
                        "name": name,
                        "pr": f"{max_weight} lbs",
                        "change": change,
                        "isNew": record is None,
                        "max": max_weight,
                    }

        return [
            {
                "name": name,
                "pr": data["pr"],
                "change": data["change"],
                "isNew": data["isNew"],
            }
            for name, data in sorted(records.items(), key=lambda item: -item[1]["max"])
        ][:4]

    def compute_period_stats(entries, start_date, end_date):
        stats = {
            "workouts": 0,
            "volume": 0,
            "avg": 0,
            "done": 0,
            "inc": 0,
            "skip": 0,
            "streak": 0,
            "streakPct": 0,
        }

        entries_by_date = {}
        total_minutes = 0
        sessions = 0

        for entry in entries:
            try:
                log_date = date.fromisoformat(entry["date"])
            except Exception:
                continue

            if log_date < start_date or log_date > end_date:
                continue

            day_log = entry.get("log", {})
            exercise_logged = False

            for ex_key, ex_data in day_log.items():
                if ex_key.startswith("__") or not isinstance(ex_data, dict):
                    continue

                status = ex_data.get("status")
                if status == "completed":
                    stats["done"] += 1
                elif status == "incomplete":
                    stats["inc"] += 1
                elif status == "skipped":
                    stats["skip"] += 1

                if status in {"completed", "incomplete", "skipped"}:
                    exercise_logged = True

                for set_data in ex_data.get("sets", []):
                    reps = set_data.get("reps") or 0
                    weight = set_data.get("weight") or 0
                    stats["volume"] += reps * weight

                total_minutes += parse_minutes(ex_data.get("time"))

            if exercise_logged:
                sessions += 1
                entries_by_date.setdefault(log_date, []).append(entry)

        stats["workouts"] = sessions
        stats["avg"] = round(total_minutes / sessions) if sessions else 0

        streak = 0
        current = end_date
        while current >= start_date:
            day_entries = entries_by_date.get(current, [])
            if not day_entries:
                break

            completed_today = any(
                isinstance(ex_data, dict) and ex_data.get("status") == "completed"
                for entry in day_entries
                for ex_key, ex_data in entry.get("log", {}).items()
                if not ex_key.startswith("__")
            )

            if not completed_today:
                break

            streak += 1
            current -= timedelta(days=1)

        period_length = (end_date - start_date).days + 1
        stats["streak"] = streak
        stats["streakPct"] = min(100, round((streak / period_length) * 100))
        return stats

    def get_volume_for_range(entries, start_date, end_date):
        total = 0
        for entry in entries:
            log_date = date.fromisoformat(entry["date"])
            if log_date < start_date or log_date > end_date:
                continue

            for ex_key, ex_data in entry.get("log", {}).items():
                if ex_key.startswith("__") or not isinstance(ex_data, dict):
                    continue

                for set_data in ex_data.get("sets", []):
                    reps = set_data.get("reps") or 0
                    weight = set_data.get("weight") or 0
                    total += reps * weight

        return total

    def build_week_labels_and_values(entries, start_date, end_date):
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        values = [0] * 7

        for entry in entries:
            log_date = date.fromisoformat(entry["date"])
            if log_date < start_date or log_date > end_date:
                continue

            day_index = entry.get("dayIndex")
            if day_index is None:
                continue

            order = [1, 2, 3, 4, 5, 6, 0]
            if day_index in order:
                values[order.index(day_index)] += 1

        return [{"l": label, "v": values[i]} for i, label in enumerate(labels)]

    def month_start(date_obj):
        return date(date_obj.year, date_obj.month, 1)

    def add_months(orig_date, months):
        total = orig_date.year * 12 + orig_date.month - 1 + months
        year, month = divmod(total, 12)
        return date(year, month + 1, 1)

    def build_monthly_data(entries, months_back):
        now_month = month_start(today)
        months = [add_months(now_month, -i) for i in range(months_back - 1, -1, -1)]
        values = []
        labels = []

        for month in months:
            next_month = add_months(month, 1)
            values.append(get_volume_for_range(entries, month, min(next_month - timedelta(days=1), today)))
            labels.append(month.strftime("%b"))

        return labels, values

    def build_period_buckets(entries, weeks_back):
        labels = [f"W{i + 1}" for i in range(weeks_back)]
        values = [0] * weeks_back
        start = today - timedelta(days=7 * weeks_back - 1)

        for entry in entries:
            log_date = date.fromisoformat(entry["date"])
            if log_date < start or log_date > today:
                continue

            diff = (log_date - start).days
            bucket = min(weeks_back - 1, diff // 7)
            values[bucket] += 1

        return labels, values


    # Calculate last period ranges
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)
    last_month_start = today - timedelta(days=59)
    last_month_end = today - timedelta(days=30)
    last_6months_start = today - timedelta(days=359)
    last_6months_end = today - timedelta(days=180)
    last_year_start = today - timedelta(days=729)
    last_year_end = today - timedelta(days=365)

    period_stats = {
        "week": compute_period_stats(all_progress_entries, week_start, today),
        "last_week": compute_period_stats(all_progress_entries, last_week_start, last_week_end),
        "month": compute_period_stats(all_progress_entries, today - timedelta(days=29), today),
        "last_month": compute_period_stats(all_progress_entries, last_month_start, last_month_end),
        "6months": compute_period_stats(all_progress_entries, today - timedelta(days=179), today),
        "last_6months": compute_period_stats(all_progress_entries, last_6months_start, last_6months_end),
        "year": compute_period_stats(all_progress_entries, today - timedelta(days=364), today),
        "last_year": compute_period_stats(all_progress_entries, last_year_start, last_year_end),
    }

    week_freq = build_week_labels_and_values(all_progress_entries, week_start, today)
    month_labels, month_vals = build_period_buckets(all_progress_entries, 5)
    six_month_labels, six_month_vals = build_monthly_data(all_progress_entries, 6)
    year_labels, year_vals = build_monthly_data(all_progress_entries, 12)

    freq_data = {
        "week": week_freq,
        "month": [{"l": label, "v": value} for label, value in zip(month_labels, month_vals)],
        "6months": [{"l": label, "v": value} for label, value in zip(six_month_labels, six_month_vals)],
        "year": [{"l": label[0], "v": value} for label, value in zip(year_labels, year_vals)],
    }

    vol_data = {
        "week": [
            get_volume_for_range(
                all_progress_entries,
                week_start + timedelta(days=i),
                week_start + timedelta(days=i),
            )
            for i in range(7)
        ],
        "month": month_vals,
        "6months": six_month_vals,
        "year": year_vals,
    }

    personal_records = build_personal_records(all_progress_entries)
    recent_workouts = build_recent_workouts(all_progress_entries)

    print("PERIOD_STATS:", period_stats)
    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={
            "user": user,
            "routines_data": routine_map,
            "progress_logs": progress_entries,
            "overview_stats": period_stats,
            "freq_data": freq_data,
            "vol_data": vol_data,
            "personal_records": personal_records,
            "recent_workouts": recent_workouts,
        },
    )


@api_router.post("/progress")
async def save_progress(progress_data: ProgressSaveRequest, db: SessionDep, user: AuthDep):
    logs = progress_data.logs or {}

    for day_key, day_log in logs.items():
        if not isinstance(day_log, dict):
            continue

        try:
            day_index = int(day_key)
        except (TypeError, ValueError):
            continue

        date_str = day_log.get("__date")
        if not date_str:
            continue

        try:
            log_date = date.fromisoformat(date_str)
        except ValueError:
            continue

        routine_id = day_log.get("__routine_id")
        payload_copy = {k: v for k, v in day_log.items() if not k.startswith("__")}
        payload_text = json.dumps(payload_copy)

        existing = db.exec(
            select(ProgressLog).where(
                ProgressLog.user_id == user.id,
                ProgressLog.log_date == log_date,
            )
        ).first()

        if existing:
            existing.day_index = day_index
            existing.routine_id = routine_id
            existing.payload = payload_text
            existing.updated_at = datetime.utcnow()
            db.add(existing)
        else:
            db.add(
                ProgressLog(
                    user_id=user.id,
                    day_index=day_index,
                    log_date=log_date,
                    routine_id=routine_id,
                    payload=payload_text,
                )
            )

    db.commit()
    return {"message": "Progress saved successfully"}