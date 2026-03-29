from __future__ import annotations

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

        # Re-sort selected tasks chronologically by time window for display
        selected.sort(key=lambda t: WINDOW_ORDER.get(t.due_window, 99))

        return selected

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
