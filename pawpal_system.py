from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List


VALID_DUE_WINDOWS = {"morning", "afternoon", "evening", "anytime"}
VALID_RECURRENCES = {"daily", "weekly", "once"}
VALID_STATUSES = {"pending", "complete", "skipped"}

# Chronological sort order for time windows
WINDOW_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "anytime": 3}


@dataclass
class OwnerProfile:
    owner_name: str
    timezone: str = "UTC"
    daily_available_minutes: int = 60
    preferred_task_times: List[str] = field(default_factory=list)
    hard_constraints: List[str] = field(default_factory=list)

    def update_profile(self, owner_name: str | None = None, timezone: str | None = None) -> None:
        """Update owner name and/or timezone, stripping whitespace and rejecting empty values."""
        if owner_name is not None:
            cleaned_name = owner_name.strip()
            if not cleaned_name:
                raise ValueError("owner_name cannot be empty")
            self.owner_name = cleaned_name

        if timezone is not None:
            cleaned_timezone = timezone.strip()
            if not cleaned_timezone:
                raise ValueError("timezone cannot be empty")
            self.timezone = cleaned_timezone

    def set_time_budget(self, minutes: int) -> None:
        """Set the owner's daily available minutes, rejecting non-positive values."""
        if minutes <= 0:
            raise ValueError("daily_available_minutes must be greater than 0")
        self.daily_available_minutes = minutes

    def set_preferences(self, preferences: List[str]) -> None:
        """Set preferred task time windows, validating each entry against allowed values."""
        normalized = [pref.lower().strip() for pref in preferences if pref.strip()]
        invalid = [pref for pref in normalized if pref not in VALID_DUE_WINDOWS]
        if invalid:
            raise ValueError(f"Unsupported preferred task times: {invalid}")
        self.preferred_task_times = normalized

    def save_to_json(
        self,
        pets: List[PetProfile],
        tasks: List[CareTask],
        file_path: str = "data.json",
    ) -> None:
        """Persist owner, pets, and tasks to a JSON file."""
        payload = {
            "owner": {
                "owner_name": self.owner_name,
                "timezone": self.timezone,
                "daily_available_minutes": self.daily_available_minutes,
                "preferred_task_times": self.preferred_task_times,
                "hard_constraints": self.hard_constraints,
            },
            "pets": [
                {
                    "pet_name": pet.pet_name,
                    "species": pet.species,
                    "breed": pet.breed,
                    "age": pet.age,
                    "energy_level": pet.energy_level,
                    "medical_notes": pet.medical_notes,
                    "routine_defaults": pet.routine_defaults,
                }
                for pet in pets
            ],
            "tasks": [
                {
                    "task_id": task.task_id,
                    "pet_name": task.pet_name,
                    "task_type": task.task_type,
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "due_window": task.due_window,
                    "recurrence": task.recurrence,
                    "status": task.status,
                    "scheduled_weekday": task.scheduled_weekday,
                    "scheduled_time": task.scheduled_time,
                }
                for task in tasks
            ],
        }

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

    @classmethod
    def load_from_json(
        cls,
        file_path: str = "data.json",
    ) -> tuple[OwnerProfile, List[PetProfile], List[CareTask]]:
        """Load owner, pets, and tasks from JSON; fall back to defaults if missing/corrupt."""
        default_owner = cls(owner_name="Jordan", daily_available_minutes=90, preferred_task_times=["morning"])
        default_pet = PetProfile(pet_name="Mochi", species="dog")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return default_owner, [default_pet], []

        owner_data = data.get("owner", {}) if isinstance(data, dict) else {}
        pets_data = data.get("pets", []) if isinstance(data, dict) else []
        tasks_data = data.get("tasks", []) if isinstance(data, dict) else []

        owner = default_owner
        if isinstance(owner_data, dict):
            try:
                owner = cls(
                    owner_name=str(owner_data.get("owner_name", default_owner.owner_name)),
                    timezone=str(owner_data.get("timezone", default_owner.timezone)),
                    daily_available_minutes=int(
                        owner_data.get("daily_available_minutes", default_owner.daily_available_minutes)
                    ),
                    preferred_task_times=list(
                        owner_data.get("preferred_task_times", default_owner.preferred_task_times)
                    ),
                    hard_constraints=list(owner_data.get("hard_constraints", default_owner.hard_constraints)),
                )
                owner.set_time_budget(owner.daily_available_minutes)
                owner.set_preferences(owner.preferred_task_times)
                owner.update_profile(owner_name=owner.owner_name, timezone=owner.timezone)
            except (TypeError, ValueError):
                owner = default_owner

        pets: List[PetProfile] = []
        if isinstance(pets_data, list):
            for pet_data in pets_data:
                if not isinstance(pet_data, dict):
                    continue
                try:
                    pet = PetProfile(
                        pet_name=str(pet_data.get("pet_name", "")).strip(),
                        species=str(pet_data.get("species", "")).strip().lower(),
                        breed=str(pet_data.get("breed", "")),
                        age=int(pet_data.get("age", 0)),
                        energy_level=str(pet_data.get("energy_level", "medium")),
                        medical_notes=str(pet_data.get("medical_notes", "")),
                        routine_defaults=list(pet_data.get("routine_defaults", [])),
                    )
                    pet.update_pet_info(pet_name=pet.pet_name, species=pet.species)
                    pets.append(pet)
                except (TypeError, ValueError):
                    continue
        if not pets:
            pets = [default_pet]

        pet_names = {pet.pet_name.lower() for pet in pets}
        tasks: List[CareTask] = []
        if isinstance(tasks_data, list):
            for task_data in tasks_data:
                if not isinstance(task_data, dict):
                    continue
                try:
                    task = CareTask(
                        task_id=str(task_data.get("task_id", "")).strip(),
                        pet_name=str(task_data.get("pet_name", "")).strip(),
                        task_type=str(task_data.get("task_type", "")).strip(),
                        duration_minutes=int(task_data.get("duration_minutes", 0)),
                        priority=int(task_data.get("priority", 0)),
                        due_window=str(task_data.get("due_window", "anytime")).strip(),
                        recurrence=str(task_data.get("recurrence", "daily")).strip(),
                        status=str(task_data.get("status", "pending")).strip(),
                        scheduled_weekday=task_data.get("scheduled_weekday"),
                        scheduled_time=str(task_data.get("scheduled_time", "")).strip(),
                    )
                except (TypeError, ValueError):
                    continue

                if task.pet_name.lower() in pet_names:
                    tasks.append(task)

        return owner, pets, tasks


@dataclass
class PetProfile:
    pet_name: str
    species: str
    breed: str = ""
    age: int = 0
    energy_level: str = "medium"
    medical_notes: str = ""
    routine_defaults: List[str] = field(default_factory=list)

    def update_pet_info(self, pet_name: str | None = None, species: str | None = None) -> None:
        """Update pet name and/or species, normalizing case and rejecting empty values."""
        if pet_name is not None:
            cleaned_name = pet_name.strip()
            if not cleaned_name:
                raise ValueError("pet_name cannot be empty")
            self.pet_name = cleaned_name

        if species is not None:
            cleaned_species = species.strip().lower()
            if not cleaned_species:
                raise ValueError("species cannot be empty")
            self.species = cleaned_species

    def get_care_needs(self) -> List[str]:
        """Return a sorted list of care activities required based on species, energy level, age, and medical notes."""
        care_needs: List[str] = []

        if self.species.lower() == "dog":
            care_needs.extend(["walk", "feeding"])
        elif self.species.lower() == "cat":
            care_needs.extend(["feeding", "litter"])
        else:
            care_needs.append("feeding")

        if self.energy_level.lower() == "high":
            care_needs.append("enrichment")

        if self.age >= 10:
            care_needs.append("gentle_activity")

        if self.medical_notes.strip():
            care_needs.append("medication_check")

        return sorted(set(care_needs))

    def flag_special_requirements(self) -> List[str]:
        """Return a list of special care flags such as senior_pet, extra_exercise, or medical_attention."""
        requirements: List[str] = []

        if self.medical_notes.strip():
            requirements.append("medical_attention")

        if self.age >= 10:
            requirements.append("senior_pet")

        if self.energy_level.lower() == "high":
            requirements.append("extra_exercise")

        return requirements


@dataclass
class CareTask:
    task_id: str
    pet_name: str
    task_type: str
    duration_minutes: int
    priority: int
    due_window: str = "anytime"
    recurrence: str = "daily"
    status: str = "pending"
    scheduled_weekday: int | None = None  # 0=Mon … 6=Sun; only used when recurrence="weekly"
    scheduled_time: str = ""              # optional wall-clock start time in "HH:MM" format

    def __post_init__(self) -> None:
        self.task_type = self.task_type.strip().lower()
        self.pet_name = self.pet_name.strip()
        self.due_window = self.due_window.strip().lower()
        self.recurrence = self.recurrence.strip().lower()
        self.status = self.status.strip().lower()

        if not self.task_id.strip():
            raise ValueError("task_id cannot be empty")
        if not self.pet_name:
            raise ValueError("pet_name cannot be empty")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")
        if self.priority < 1 or self.priority > 5:
            raise ValueError("priority must be between 1 and 5")
        if self.due_window not in VALID_DUE_WINDOWS:
            raise ValueError(f"due_window must be one of {sorted(VALID_DUE_WINDOWS)}")
        if self.recurrence not in VALID_RECURRENCES:
            raise ValueError(f"recurrence must be one of {sorted(VALID_RECURRENCES)}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        if self.recurrence == "weekly" and self.scheduled_weekday is None:
            raise ValueError("weekly tasks must set scheduled_weekday (0=Mon … 6=Sun)")
        if self.scheduled_weekday is not None and not (0 <= self.scheduled_weekday <= 6):
            raise ValueError("scheduled_weekday must be 0–6")
        if self.scheduled_time:
            parts = self.scheduled_time.split(":")
            if (
                len(parts) != 2
                or not parts[0].isdigit()
                or not parts[1].isdigit()
                or not (0 <= int(parts[0]) <= 23)
                or not (0 <= int(parts[1]) <= 59)
            ):
                raise ValueError("scheduled_time must be in HH:MM format (e.g. '08:30')")

    def edit_task(self, **updates) -> None:
        """Apply keyword updates to task fields and re-validate all constraints."""
        for key, value in updates.items():
            if not hasattr(self, key):
                raise ValueError(f"Unknown task field: {key}")
            setattr(self, key, value)

        self.__post_init__()

    def mark_complete(self) -> None:
        """Set the task status to 'complete'."""
        self.status = "complete"

    def mark_skipped(self) -> None:
        """Set the task status to 'skipped'."""
        self.status = "skipped"

    @property
    def priority_level(self) -> str:
        """Return a human-readable priority label based on numeric priority."""
        if self.priority >= 5:
            return "High"
        if self.priority >= 3:
            return "Medium"
        return "Low"

    def is_due_today(self, weekday: int | None = None) -> bool:
        """Return True if the task is pending and due on the given weekday (0=Mon…6=Sun).

        - daily / once tasks are always due when pending.
        - weekly tasks are due only when weekday matches scheduled_weekday.
          If weekday is None, weekly tasks are never considered due.
        """
        if self.status != "pending":
            return False
        if self.recurrence == "daily":
            return True
        if self.recurrence == "once":
            return True
        if self.recurrence == "weekly":
            return weekday is not None and weekday == self.scheduled_weekday
        return False


class Scheduler:
    WINDOW_TIME_RANGES = {
        "morning": (7 * 60, 12 * 60),
        "afternoon": (12 * 60, 17 * 60),
        "evening": (17 * 60, 22 * 60),
        "anytime": (7 * 60, 22 * 60),
    }

    def __init__(
        self,
        scheduling_rules: List[str] | None = None,
        priority_weights: Dict[str, int] | None = None,
        constraint_settings: List[str] | None = None,
    ) -> None:
        self.scheduling_rules = scheduling_rules or []
        self.priority_weights = priority_weights or {}
        self.constraint_settings = constraint_settings or []
        self._last_explanations: Dict[str, str] = {}
        self._last_conflicts: List[str] = []

    def generate_plan(
        self,
        owner: OwnerProfile,
        pet: PetProfile,
        tasks: List[CareTask],
        weekday: int | None = None,
    ) -> List[CareTask]:
        """Select today's tasks for a pet, resolve conflicts, rank by score, and return sorted by time window."""
        filtered = [
            task
            for task in tasks
            if task.pet_name.lower() == pet.pet_name.lower() and task.is_due_today(weekday)
        ]

        candidate_tasks = self.resolve_conflicts(filtered)

        preferred_windows = set(owner.preferred_task_times)

        def score_key(task: CareTask) -> int:
            preference_bonus = 1 if task.due_window in preferred_windows else 0
            return self.score_task(task) + preference_bonus

        ranked = sorted(candidate_tasks, key=score_key, reverse=True)

        selected: List[CareTask] = []
        used_minutes = 0
        self._last_explanations = {}

        for task in ranked:
            projected_time = used_minutes + task.duration_minutes
            if projected_time <= owner.daily_available_minutes:
                selected.append(task)
                used_minutes = projected_time
                self._last_explanations[task.task_id] = self.explain_decision(task)

        selected.sort(key=lambda t: WINDOW_ORDER.get(t.due_window, 99))
        selected = self.assign_next_available_slots(selected)
        return self.sort_by_priority_then_time(selected)

    @staticmethod
    def _to_minutes(hhmm: str) -> int:
        hour, minute = hhmm.split(":")
        return int(hour) * 60 + int(minute)

    @staticmethod
    def _to_hhmm(total_minutes: int) -> str:
        hour = total_minutes // 60
        minute = total_minutes % 60
        return f"{hour:02d}:{minute:02d}"

    def _find_next_slot(
        self,
        duration_minutes: int,
        range_start: int,
        range_end: int,
        occupied_intervals: List[tuple[int, int]],
    ) -> int | None:
        cursor = range_start
        overlapping = sorted(
            (start, end)
            for start, end in occupied_intervals
            if end > range_start and start < range_end
        )

        for start, end in overlapping:
            if cursor + duration_minutes <= start:
                return cursor
            cursor = max(cursor, end)

        if cursor + duration_minutes <= range_end:
            return cursor
        return None

    def assign_next_available_slots(self, tasks: List[CareTask]) -> List[CareTask]:
        occupied_intervals: List[tuple[int, int]] = []
        for task in tasks:
            if not task.scheduled_time:
                continue
            start = self._to_minutes(task.scheduled_time)
            occupied_intervals.append((start, start + task.duration_minutes))

        for task in tasks:
            if task.scheduled_time:
                continue

            range_start, range_end = self.WINDOW_TIME_RANGES.get(
                task.due_window,
                self.WINDOW_TIME_RANGES["anytime"],
            )
            slot = self._find_next_slot(
                task.duration_minutes,
                range_start,
                range_end,
                occupied_intervals,
            )

            if slot is None:
                fallback_start, fallback_end = self.WINDOW_TIME_RANGES["anytime"]
                slot = self._find_next_slot(
                    task.duration_minutes,
                    fallback_start,
                    fallback_end,
                    occupied_intervals,
                )

            if slot is not None:
                task.scheduled_time = self._to_hhmm(slot)
                occupied_intervals.append((slot, slot + task.duration_minutes))

        return tasks

    def resolve_conflicts(self, tasks: List[CareTask]) -> List[CareTask]:
        """Deduplicate same-type tasks per pet, keeping the highest-priority one; warn on cross-window duplicates."""
        self._last_conflicts = []

        # First pass: detect same task_type across ANY window for the same pet
        type_seen: Dict[tuple[str, str], List[CareTask]] = {}
        for task in tasks:
            key = (task.pet_name.lower(), task.task_type)
            type_seen.setdefault(key, []).append(task)

        for (pet_name, task_type), group in type_seen.items():
            windows = [t.due_window for t in group]
            if len(set(windows)) > 1:
                self._last_conflicts.append(
                    f"WARNING: '{task_type}' for {pet_name} appears in multiple windows: {windows}. "
                    f"Keeping highest-priority entry."
                )

        # Second pass: keep only the best task per pet/type (across all windows)
        best: Dict[tuple[str, str], CareTask] = {}
        for task in tasks:
            key = (task.pet_name.lower(), task.task_type)
            existing = best.get(key)
            if existing is None:
                best[key] = task
            elif task.priority > existing.priority:
                best[key] = task
            elif task.priority == existing.priority and task.duration_minutes < existing.duration_minutes:
                best[key] = task

        return list(best.values())

    def detect_time_conflicts(self, tasks: List[CareTask]) -> List[str]:
        """Return warning strings for any tasks that share the same scheduled_time; never raises."""
        warnings: List[str] = []
        time_slots: Dict[str, List[CareTask]] = {}

        for task in tasks:
            if not task.scheduled_time:
                continue
            time_slots.setdefault(task.scheduled_time, []).append(task)

        for time, clashing in time_slots.items():
            if len(clashing) > 1:
                labels = ", ".join(
                    f"{t.task_type} ({t.pet_name})" for t in clashing
                )
                warnings.append(
                    f"WARNING: {len(clashing)} tasks overlap at {time} -> {labels}"
                )

        return warnings

    def sort_by_time(self, tasks: List[CareTask]) -> List[CareTask]:
        """Return tasks sorted by scheduled_time (HH:MM); tasks without a time sort to the end."""
        return sorted(
            tasks,
            key=lambda task: task.scheduled_time if task.scheduled_time else "99:99"
        )

    def sort_by_priority_then_time(self, tasks: List[CareTask]) -> List[CareTask]:
        """Return tasks sorted by priority (high to low), then scheduled_time (earliest first)."""
        return sorted(
            tasks,
            key=lambda task: (
                -task.priority,
                task.scheduled_time if task.scheduled_time else "99:99",
            ),
        )

    def get_last_conflicts(self) -> List[str]:
        """Return conflict warnings raised during the most recent resolve_conflicts call."""
        return list(self._last_conflicts)

    def score_task(self, task: CareTask) -> int:
        """Compute a numeric score for a task based on priority, type weight, window specificity, and task type."""
        score = task.priority * 10
        score += self.priority_weights.get(task.task_type, 0)

        if task.due_window != "anytime":
            score += 2

        if task.task_type in {"medication", "vet_appointment"}:
            score += 5

        return score

    def explain_decision(self, task: CareTask) -> str:
        """Return a human-readable string explaining why a task was included in the plan."""
        weighted = self.priority_weights.get(task.task_type, 0)
        due_note = "fixed time window" if task.due_window != "anytime" else "flexible timing"
        recurrence_note = f"recurs {task.recurrence}"
        return (
            f"Selected {task.task_type} for {task.pet_name} (priority {task.priority}, "
            f"duration {task.duration_minutes}m, {due_note}, {recurrence_note}, type weight {weighted})."
        )

    def get_last_explanations(self) -> Dict[str, str]:
        """Return a copy of the explanations generated during the most recent plan."""
        return dict(self._last_explanations)


class PawPalSystem:
    def __init__(self, owner: OwnerProfile, pets: List[PetProfile], scheduler: Scheduler) -> None:
        self.owner = owner
        self.pets = pets
        self.scheduler = scheduler
        self.tasks: List[CareTask] = []

    def add_task(self, task: CareTask) -> None:
        """Add a task to the system, rejecting unknown pets or duplicate task IDs."""
        pet_names = {pet.pet_name.lower() for pet in self.pets}
        if task.pet_name.lower() not in pet_names:
            raise ValueError(f"Unknown pet_name '{task.pet_name}' for task {task.task_id}")

        if any(existing.task_id == task.task_id for existing in self.tasks):
            raise ValueError(f"Duplicate task_id '{task.task_id}'")

        self.tasks.append(task)

    def get_tasks_for_pet(self, pet_name: str) -> List[CareTask]:
        """Return all tasks assigned to the given pet (case-insensitive)."""
        return [task for task in self.tasks if task.pet_name.lower() == pet_name.lower()]

    def filter_tasks(
        self,
        status: str | None = None,
        pet_name: str | None = None,
    ) -> List[CareTask]:
        """Return tasks filtered by status and/or pet name; both filters are optional and combinable."""
        results = self.tasks
        if status is not None:
            if status not in VALID_STATUSES:
                raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
            results = [t for t in results if t.status == status]
        if pet_name is not None:
            results = [t for t in results if t.pet_name.lower() == pet_name.lower()]
        return results

    def get_tasks_by_status(self, status: str) -> List[CareTask]:
        """Return all tasks across all pets that match the given status (pending/complete/skipped)."""
        if status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        return [task for task in self.tasks if task.status == status]

    def get_tasks_for_window(self, window: str) -> List[CareTask]:
        """Return all pending tasks across all pets scheduled for the given time window."""
        if window not in VALID_DUE_WINDOWS:
            raise ValueError(f"window must be one of {sorted(VALID_DUE_WINDOWS)}")
        return [task for task in self.tasks if task.due_window == window and task.status == "pending"]

    def reset_for_new_day(self) -> List[CareTask]:
        """Reset all completed or skipped daily tasks back to pending, simulating the start of a new day.

        Returns the list of tasks that were reset so callers can inspect or log them.
        Weekly and once-off tasks are left untouched.
        """
        reset: List[CareTask] = []
        for task in self.tasks:
            if task.recurrence == "daily" and task.status in {"complete", "skipped"}:
                task.status = "pending"
                reset.append(task)
        return reset

    def generate_daily_plan(self, pet_name: str, weekday: int | None = None) -> List[CareTask]:
        """Generate and return the scheduler's prioritized daily plan for the named pet."""
        pet = next((candidate for candidate in self.pets if candidate.pet_name.lower() == pet_name.lower()), None)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' not found")

        tasks = self.get_tasks_for_pet(pet_name)
        return self.scheduler.generate_plan(self.owner, pet, tasks, weekday=weekday)
