from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class OwnerProfile:
    owner_name: str
    timezone: str = "UTC"
    daily_available_minutes: int = 60
    preferred_task_times: List[str] = field(default_factory=list)
    hard_constraints: List[str] = field(default_factory=list)

    def update_profile(self, owner_name: str | None = None, timezone: str | None = None) -> None:
        pass

    def set_time_budget(self, minutes: int) -> None:
        pass

    def set_preferences(self, preferences: List[str]) -> None:
        pass


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
        pass

    def get_care_needs(self) -> List[str]:
        pass

    def flag_special_requirements(self) -> List[str]:
        pass


@dataclass
class CareTask:
    task_id: str
    task_type: str
    duration_minutes: int
    priority: int
    due_window: str = "anytime"
    recurrence: str = "daily"
    status: str = "pending"

    def edit_task(self, **updates) -> None:
        pass

    def mark_complete(self) -> None:
        pass

    def mark_skipped(self) -> None:
        pass

    def is_due_today(self) -> bool:
        pass


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

    def generate_plan(
        self,
        owner: OwnerProfile,
        pet: PetProfile,
        tasks: List[CareTask],
    ) -> List[CareTask]:
        pass

    def resolve_conflicts(self, tasks: List[CareTask]) -> List[CareTask]:
        pass

    def score_task(self, task: CareTask) -> int:
        pass

    def explain_decision(self, task: CareTask) -> str:
        pass
