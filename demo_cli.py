from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler


def build_demo_system() -> PawPalSystem:
    owner = OwnerProfile(
        owner_name="Jordan",
        timezone="UTC",
        daily_available_minutes=50,
        preferred_task_times=["morning", "evening"],
    )

    pet = PetProfile(
        pet_name="Mochi",
        species="dog",
        age=4,
        energy_level="high",
    )

    scheduler = Scheduler(priority_weights={"medication": 8, "walk": 3, "feeding": 5})
    system = PawPalSystem(owner=owner, pets=[pet], scheduler=scheduler)

    system.add_task(CareTask("t1", "Mochi", "feeding", 10, 5, due_window="morning"))
    system.add_task(CareTask("t2", "Mochi", "walk", 25, 4, due_window="evening"))
    system.add_task(CareTask("t3", "Mochi", "medication", 5, 5, due_window="morning"))
    system.add_task(CareTask("t4", "Mochi", "enrichment", 20, 3, due_window="anytime"))

    return system


def main() -> None:
    system = build_demo_system()
    plan = system.generate_daily_plan("Mochi")
    explanations = system.scheduler.get_last_explanations()

    print("=== PawPal+ Daily Plan (CLI Demo) ===")
    if not plan:
        print("No tasks selected for today.")
        return

    total_minutes = sum(task.duration_minutes for task in plan)
    for index, task in enumerate(plan, start=1):
        print(
            f"{index}. {task.task_type.title()} | duration={task.duration_minutes}m "
            f"| priority={task.priority} | window={task.due_window}"
        )
        print(f"   reason: {explanations.get(task.task_id, 'No explanation available')}" )

    print(f"Total planned time: {total_minutes} minutes")


if __name__ == "__main__":
    main()
