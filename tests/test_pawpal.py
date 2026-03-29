from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should set status to 'complete'."""
    task = CareTask("t1", "Mochi", "walk", 20, priority=3)
    assert task.status == "pending"

    task.mark_complete()

    assert task.status == "complete"


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to the system increases that pet's task count."""
    owner = OwnerProfile(owner_name="Jordan", daily_available_minutes=60)
    pet = PetProfile(pet_name="Mochi", species="dog")
    system = PawPalSystem(owner=owner, pets=[pet], scheduler=Scheduler())

    assert len(system.get_tasks_for_pet("Mochi")) == 0

    system.add_task(CareTask("t1", "Mochi", "feeding", 10, priority=4))

    assert len(system.get_tasks_for_pet("Mochi")) == 1
