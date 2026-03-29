from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


VALID_DUE_WINDOWS = {"morning", "afternoon", "evening", "anytime"}
VALID_RECURRENCES = {"daily", "weekly", "once"}
VALID_STATUSES = {"pending", "complete", "skipped"}


@dataclass
class OwnerProfile:
    owner_name: str
    timezone: str = "UTC"
    daily_available_minutes: int = 60
    preferred_task_times: List[str] = field(default_factory=list)
    hard_constraints: List[str] = field(default_factory=list)

    def update_profile(self, owner_name: str | None = None, timezone: str | None = None) -> None:
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
        if minutes <= 0:
            raise ValueError("daily_available_minutes must be greater than 0")
        self.daily_available_minutes = minutes

    def set_preferences(self, preferences: List[str]) -> None:
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

    def edit_task(self, **updates) -> None:
        for key, value in updates.items():
            if not hasattr(self, key):
                raise ValueError(f"Unknown task field: {key}")
            setattr(self, key, value)

        self.__post_init__()

    def mark_complete(self) -> None:
        self.status = "complete"

    def mark_skipped(self) -> None:
        self.status = "skipped"

    def is_due_today(self) -> bool:
        return self.status == "pending" and self.recurrence in {"daily", "once"}


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

    def generate_plan(
        self,
        owner: OwnerProfile,
        pet: PetProfile,
        tasks: List[CareTask],
    ) -> List[CareTask]:
        filtered = [
            task
            for task in tasks
            if task.pet_name.lower() == pet.pet_name.lower() and task.is_due_today()
        ]

        candidate_tasks = self.resolve_conflicts(filtered)

        preferred_windows = set(owner.preferred_task_times)

        def sort_key(task: CareTask) -> tuple[int, int, int]:
            preference_bonus = 1 if task.due_window in preferred_windows else 0
            return (self.score_task(task) + preference_bonus, task.priority, -task.duration_minutes)

        ranked = sorted(candidate_tasks, key=sort_key, reverse=True)

        selected: List[CareTask] = []
        used_minutes = 0
        self._last_explanations = {}

        for task in ranked:
            projected_time = used_minutes + task.duration_minutes
            if projected_time <= owner.daily_available_minutes:
                selected.append(task)
                used_minutes = projected_time
                self._last_explanations[task.task_id] = self.explain_decision(task)

        return selected

    def resolve_conflicts(self, tasks: List[CareTask]) -> List[CareTask]:
        deduped: Dict[tuple[str, str, str], CareTask] = {}

        for task in tasks:
            key = (task.pet_name.lower(), task.task_type, task.due_window)
            existing = deduped.get(key)

            if existing is None:
                deduped[key] = task
                continue

            if task.priority > existing.priority:
                deduped[key] = task
                continue

            if task.priority == existing.priority and task.duration_minutes < existing.duration_minutes:
                deduped[key] = task

        return list(deduped.values())

    def score_task(self, task: CareTask) -> int:
        score = task.priority * 10
        score += self.priority_weights.get(task.task_type, 0)

        if task.due_window != "anytime":
            score += 2

        if task.task_type in {"medication", "vet_appointment"}:
            score += 5

        return score

    def explain_decision(self, task: CareTask) -> str:
        weighted = self.priority_weights.get(task.task_type, 0)
        due_note = "fixed time window" if task.due_window != "anytime" else "flexible timing"
        return (
            f"Selected {task.task_type} for {task.pet_name} (priority {task.priority}, "
            f"duration {task.duration_minutes}m, {due_note}, type weight {weighted})."
        )

    def get_last_explanations(self) -> Dict[str, str]:
        return dict(self._last_explanations)


class PawPalSystem:
    def __init__(self, owner: OwnerProfile, pets: List[PetProfile], scheduler: Scheduler) -> None:
        self.owner = owner
        self.pets = pets
        self.scheduler = scheduler
        self.tasks: List[CareTask] = []

    def add_task(self, task: CareTask) -> None:
        pet_names = {pet.pet_name.lower() for pet in self.pets}
        if task.pet_name.lower() not in pet_names:
            raise ValueError(f"Unknown pet_name '{task.pet_name}' for task {task.task_id}")

        if any(existing.task_id == task.task_id for existing in self.tasks):
            raise ValueError(f"Duplicate task_id '{task.task_id}'")

        self.tasks.append(task)

    def get_tasks_for_pet(self, pet_name: str) -> List[CareTask]:
        return [task for task in self.tasks if task.pet_name.lower() == pet_name.lower()]

    def generate_daily_plan(self, pet_name: str) -> List[CareTask]:
        pet = next((candidate for candidate in self.pets if candidate.pet_name.lower() == pet_name.lower()), None)
        if pet is None:
            raise ValueError(f"Pet '{pet_name}' not found")

        tasks = self.get_tasks_for_pet(pet_name)
        return self.scheduler.generate_plan(self.owner, pet, tasks)
