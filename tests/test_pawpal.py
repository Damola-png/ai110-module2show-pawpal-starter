import pytest

from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler


# ── helpers ──────────────────────────────────────────────────────────────────

def make_system(minutes: int = 120) -> PawPalSystem:
    owner = OwnerProfile(owner_name="Jordan", daily_available_minutes=minutes)
    pet = PetProfile(pet_name="Mochi", species="dog")
    return PawPalSystem(owner=owner, pets=[pet], scheduler=Scheduler())


# ── original tests (kept) ─────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should set status to 'complete'."""
    task = CareTask("t1", "Mochi", "walk", 20, priority=3)
    assert task.status == "pending"
    task.mark_complete()
    assert task.status == "complete"


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to the system increases that pet's task count."""
    system = make_system()
    assert len(system.get_tasks_for_pet("Mochi")) == 0
    system.add_task(CareTask("t1", "Mochi", "feeding", 10, priority=4))
    assert len(system.get_tasks_for_pet("Mochi")) == 1


# ── sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order():
    """Happy path: tasks added out of order come back sorted earliest → latest."""
    scheduler = Scheduler()
    tasks = [
        CareTask("c", "Mochi", "litter",    10, priority=2, scheduled_time="14:00"),
        CareTask("a", "Mochi", "walk",       30, priority=4, scheduled_time="07:30"),
        CareTask("b", "Mochi", "medication",  5, priority=5, scheduled_time="08:00"),
    ]

    result = scheduler.sort_by_time(tasks)

    assert [t.task_id for t in result] == ["a", "b", "c"]


def test_sort_by_time_untimed_tasks_go_last():
    """Edge case: tasks with no scheduled_time should sort after all timed tasks."""
    scheduler = Scheduler()
    tasks = [
        CareTask("no-time", "Mochi", "enrichment", 20, priority=3),
        CareTask("timed",   "Mochi", "walk",        30, priority=4, scheduled_time="07:30"),
    ]

    result = scheduler.sort_by_time(tasks)

    assert result[0].task_id == "timed"
    assert result[-1].task_id == "no-time"


def test_sort_by_time_all_untimed_returns_same_count():
    """Edge case: a list where no task has a scheduled_time still returns all tasks."""
    scheduler = Scheduler()
    tasks = [
        CareTask("x", "Mochi", "walk",    30, priority=4),
        CareTask("y", "Mochi", "feeding", 10, priority=5),
    ]

    result = scheduler.sort_by_time(tasks)

    assert len(result) == 2


def test_priority_level_labels_are_derived_from_numeric_priority():
    low = CareTask("low", "Mochi", "feeding", 10, priority=2)
    medium = CareTask("med", "Mochi", "walk", 20, priority=3)
    high = CareTask("high", "Mochi", "medication", 5, priority=5)

    assert low.priority_level == "Low"
    assert medium.priority_level == "Medium"
    assert high.priority_level == "High"


def test_sort_by_priority_then_time_orders_high_first_then_earlier_time():
    scheduler = Scheduler()
    tasks = [
        CareTask("a", "Mochi", "feeding", 10, priority=3, scheduled_time="07:30"),
        CareTask("b", "Mochi", "walk", 30, priority=5, scheduled_time="08:30"),
        CareTask("c", "Mochi", "medication", 5, priority=5, scheduled_time="08:00"),
    ]

    result = scheduler.sort_by_priority_then_time(tasks)

    assert [task.task_id for task in result] == ["c", "b", "a"]


def test_assign_next_available_slots_sets_time_for_untimed_tasks():
    """Untimed tasks should receive a concrete HH:MM start time in due-window order."""
    scheduler = Scheduler()
    tasks = [
        CareTask("a", "Mochi", "walk", 30, priority=4, due_window="morning"),
        CareTask("b", "Mochi", "feeding", 10, priority=5, due_window="morning"),
    ]

    result = scheduler.assign_next_available_slots(tasks)

    assert result[0].scheduled_time == "07:00"
    assert result[1].scheduled_time == "07:30"


def test_assign_next_available_slots_respects_existing_timed_tasks():
    """Untimed tasks should be placed in the next gap after already-timed intervals."""
    scheduler = Scheduler()
    tasks = [
        CareTask("existing", "Mochi", "medication", 20, priority=5, due_window="morning", scheduled_time="07:00"),
        CareTask("new", "Mochi", "walk", 30, priority=4, due_window="morning"),
    ]

    result = scheduler.assign_next_available_slots(tasks)

    assert result[1].scheduled_time == "07:20"


# ── recurrence logic ──────────────────────────────────────────────────────────

def test_daily_task_excluded_from_plan_when_complete():
    """Happy path: a completed daily task is not pending, so it is excluded from today's plan."""
    system = make_system()
    system.add_task(CareTask("walk", "Mochi", "walk", 30, priority=4))
    system.tasks[0].mark_complete()

    plan = system.generate_daily_plan("Mochi")

    assert all(t.task_id != "walk" for t in plan)


def test_reset_for_new_day_restores_daily_task_to_pending():
    """Recurrence: after reset_for_new_day(), a completed daily task becomes pending again."""
    system = make_system()
    system.add_task(CareTask("walk", "Mochi", "walk", 30, priority=4))
    system.tasks[0].mark_complete()
    assert system.tasks[0].status == "complete"

    system.reset_for_new_day()

    assert system.tasks[0].status == "pending"


def test_reset_for_new_day_includes_task_in_next_plan():
    """Recurrence: after reset_for_new_day(), the previously completed task re-enters the plan."""
    system = make_system()
    system.add_task(CareTask("walk", "Mochi", "walk", 30, priority=4))
    system.tasks[0].mark_complete()
    system.reset_for_new_day()

    plan = system.generate_daily_plan("Mochi")

    assert any(t.task_id == "walk" for t in plan)


def test_weekly_task_appears_only_on_correct_weekday():
    """Recurrence: a weekly task scheduled for Saturday (5) is excluded on other days."""
    system = make_system()
    system.add_task(CareTask("groom", "Mochi", "grooming", 15, priority=3,
                              recurrence="weekly", scheduled_weekday=5))

    plan_friday   = system.generate_daily_plan("Mochi", weekday=4)
    plan_saturday = system.generate_daily_plan("Mochi", weekday=5)

    assert all(t.task_id != "groom" for t in plan_friday)
    assert any(t.task_id == "groom" for t in plan_saturday)


def test_weekly_task_excluded_when_weekday_is_none():
    """Edge case: weekly task is never due when no weekday is passed to generate_daily_plan."""
    system = make_system()
    system.add_task(CareTask("groom", "Mochi", "grooming", 15, priority=3,
                              recurrence="weekly", scheduled_weekday=5))

    plan = system.generate_daily_plan("Mochi", weekday=None)

    assert plan == []


# ── conflict detection ────────────────────────────────────────────────────────

def test_detect_time_conflicts_flags_same_start_time():
    """Happy path: two tasks at the same HH:MM produce one warning string."""
    scheduler = Scheduler()
    tasks = [
        CareTask("a", "Mochi", "walk",    30, priority=4, scheduled_time="08:00"),
        CareTask("b", "Luna",  "feeding", 10, priority=5, scheduled_time="08:00"),
    ]

    warnings = scheduler.detect_time_conflicts(tasks)

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_time_conflicts_returns_empty_when_no_overlap():
    """Edge case: tasks at distinct times produce no warnings."""
    scheduler = Scheduler()
    tasks = [
        CareTask("a", "Mochi", "walk",    30, priority=4, scheduled_time="07:30"),
        CareTask("b", "Mochi", "feeding", 10, priority=5, scheduled_time="08:30"),
    ]

    warnings = scheduler.detect_time_conflicts(tasks)

    assert warnings == []


def test_detect_time_conflicts_ignores_tasks_without_scheduled_time():
    """Edge case: tasks with no scheduled_time are skipped — no false positives."""
    scheduler = Scheduler()
    tasks = [
        CareTask("a", "Mochi", "walk",    30, priority=4),
        CareTask("b", "Mochi", "feeding", 10, priority=5),
    ]

    warnings = scheduler.detect_time_conflicts(tasks)

    assert warnings == []


def test_detect_time_conflicts_does_not_raise():
    """Edge case: detect_time_conflicts() never raises, even with an empty list."""
    scheduler = Scheduler()

    warnings = scheduler.detect_time_conflicts([])

    assert warnings == []


# ── pet with no tasks ─────────────────────────────────────────────────────────

def test_generate_plan_for_pet_with_no_tasks_returns_empty():
    """Edge case: a pet registered in the system but with zero tasks yields an empty plan."""
    system = make_system()

    plan = system.generate_daily_plan("Mochi")

    assert plan == []


# ── filter_tasks ──────────────────────────────────────────────────────────────

def test_filter_tasks_by_status_returns_only_matching():
    """Happy path: filter_tasks(status='complete') returns only completed tasks."""
    system = make_system()
    system.add_task(CareTask("a", "Mochi", "walk",    30, priority=4))
    system.add_task(CareTask("b", "Mochi", "feeding", 10, priority=5))
    system.tasks[0].mark_complete()

    result = system.filter_tasks(status="complete")

    assert len(result) == 1
    assert result[0].task_id == "a"


def test_filter_tasks_combined_status_and_pet():
    """Happy path: filter_tasks with both status and pet_name returns the intersection."""
    owner = OwnerProfile(owner_name="Jordan", daily_available_minutes=60)
    mochi = PetProfile(pet_name="Mochi", species="dog")
    luna  = PetProfile(pet_name="Luna",  species="cat")
    system = PawPalSystem(owner=owner, pets=[mochi, luna], scheduler=Scheduler())

    system.add_task(CareTask("m1", "Mochi", "walk",    30, priority=4))
    system.add_task(CareTask("l1", "Luna",  "feeding", 10, priority=5))
    system.tasks[0].mark_complete()  # only Mochi's task is complete

    result = system.filter_tasks(status="complete", pet_name="Mochi")

    assert len(result) == 1
    assert result[0].task_id == "m1"
