from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None


RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"

TASK_EMOJIS = {
    "walk": "🐕",
    "feeding": "🍽️",
    "medication": "💊",
    "enrichment": "🧩",
    "grooming": "✂️",
    "vet_appointment": "🩺",
}


def _color(text: str, color_code: str) -> str:
    return f"{color_code}{text}{RESET}"


def _priority_badge(priority: int) -> str:
    if priority >= 5:
        return _color("🔴 High", RED)
    if priority >= 3:
        return _color("🟡 Medium", YELLOW)
    return _color("🟢 Low", GREEN)


def _status_badge(status: str) -> str:
    normalized = status.lower()
    if normalized == "complete":
        return _color("✅ Complete", GREEN)
    if normalized == "skipped":
        return _color("⏭️ Skipped", BLUE)
    return _color("⏳ Pending", YELLOW)


def _print_schedule_table(plan: list[CareTask]) -> None:
    rows = []
    for index, task in enumerate(plan, start=1):
        emoji = TASK_EMOJIS.get(task.task_type, "🐾")
        rows.append(
            {
                "#": index,
                "Time": task.scheduled_time if task.scheduled_time else "--:--",
                "Task": f"{emoji} {task.task_type.replace('_', ' ').title()}",
                "Window": task.due_window.title(),
                "Duration": f"{task.duration_minutes}m",
                "Priority": _priority_badge(task.priority),
                "Status": _status_badge(task.status),
            }
        )

    if tabulate is not None:
        print(tabulate(rows, headers="keys", tablefmt="fancy_grid"))
        return

    headers = ["#", "Time", "Task", "Window", "Duration", "Priority", "Status"]
    print(" | ".join(headers))
    print("-" * 90)
    for row in rows:
        print(" | ".join(str(row[key]) for key in headers))


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

    print(_color("\n=== 🐾 PawPal+ Daily Plan (CLI Demo) ===", BLUE))
    if not plan:
        print("No tasks selected for today.")
        return

    _print_schedule_table(plan)

    print("\n💡 Why each task was selected")
    for task in plan:
        emoji = TASK_EMOJIS.get(task.task_type, "🐾")
        reason = explanations.get(task.task_id, "No explanation available")
        print(f"- {emoji} {task.task_type.replace('_', ' ').title()}: {reason}")

    total_minutes = sum(task.duration_minutes for task in plan)
    print(f"\n🕒 Total planned time: {total_minutes} minutes")


if __name__ == "__main__":
    main()
