import pytest

from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler


def make_system(minutes: int = 40) -> PawPalSystem:
    owner = OwnerProfile(
        owner_name="Jordan",
        daily_available_minutes=minutes,
        preferred_task_times=["morning"],
    )
    pet = PetProfile(pet_name="Mochi", species="dog")
    scheduler = Scheduler(priority_weights={"medication": 10, "walk": 3})
    return PawPalSystem(owner=owner, pets=[pet], scheduler=scheduler)


def test_generate_plan_respects_time_budget() -> None:
    system = make_system(minutes=30)
    system.add_task(CareTask("a", "Mochi", "walk", 25, 4, due_window="morning"))
    system.add_task(CareTask("b", "Mochi", "feeding", 15, 5, due_window="morning"))
    system.add_task(CareTask("c", "Mochi", "medication", 5, 5, due_window="morning"))

    plan = system.generate_daily_plan("Mochi")

    assert sum(task.duration_minutes for task in plan) <= 30


def test_conflict_resolution_keeps_higher_priority_duplicate() -> None:
    scheduler = Scheduler()
    low = CareTask("a", "Mochi", "walk", 20, 2, due_window="morning")
    high = CareTask("b", "Mochi", "walk", 25, 5, due_window="morning")

    resolved = scheduler.resolve_conflicts([low, high])

    assert len(resolved) == 1
    assert resolved[0].task_id == "b"


def test_unknown_pet_task_rejected() -> None:
    system = make_system()

    with pytest.raises(ValueError):
        system.add_task(CareTask("x", "Luna", "feeding", 10, 3))


def test_generate_plan_returns_explanations() -> None:
    system = make_system(minutes=60)
    system.add_task(CareTask("a", "Mochi", "medication", 5, 5, due_window="morning"))

    plan = system.generate_daily_plan("Mochi")
    explanations = system.scheduler.get_last_explanations()

    assert len(plan) == 1
    assert "priority" in explanations["a"]
