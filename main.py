from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler

# --- Setup ---
owner = OwnerProfile(
    owner_name="Jordan",
    daily_available_minutes=90,
    preferred_task_times=["morning"],
)

mochi = PetProfile(pet_name="Mochi", species="dog", energy_level="high", age=3)
luna = PetProfile(pet_name="Luna", species="cat", age=11, medical_notes="joint supplement")

scheduler = Scheduler(priority_weights={"medication": 10, "walk": 3, "feeding": 2})
system = PawPalSystem(owner=owner, pets=[mochi, luna], scheduler=scheduler)

# --- Tasks for Mochi ---
system.add_task(CareTask("mochi-walk",     "Mochi", "walk",     30, priority=4, due_window="morning"))
system.add_task(CareTask("mochi-feed-am",  "Mochi", "feeding",  10, priority=5, due_window="morning"))
system.add_task(CareTask("mochi-enrichment", "Mochi", "enrichment", 20, priority=3, due_window="afternoon"))

# --- Tasks for Luna ---
system.add_task(CareTask("luna-feed-am",   "Luna", "feeding",   10, priority=5, due_window="morning"))
system.add_task(CareTask("luna-medication","Luna", "medication",  5, priority=5, due_window="morning"))
system.add_task(CareTask("luna-litter",    "Luna", "litter",    10, priority=3, due_window="anytime"))

# --- Generate & Print Plans ---
def print_schedule(pet_name: str) -> None:
    plan = system.generate_daily_plan(pet_name)
    explanations = system.scheduler.get_last_explanations()
    total = sum(t.duration_minutes for t in plan)

    print(f"\n  {pet_name}'s Tasks")
    print(f"  {'-' * 40}")
    if not plan:
        print("  No tasks scheduled.")
    else:
        for task in plan:
            window = f"[{task.due_window}]".ljust(13)
            reason = explanations.get(task.task_id, "")
            print(f"  {window}  {task.task_type:<18}  {task.duration_minutes:>3} min  (priority {task.priority})")
            print(f"             > {reason}")
    print(f"\n  Total time: {total} min")


print("=" * 50)
print("   TODAY'S SCHEDULE  -  PawPal+")
print(f"   Owner: {owner.owner_name}  |  Budget: {owner.daily_available_minutes} min")
print("=" * 50)

for pet in system.pets:
    print_schedule(pet.pet_name)

print("\n" + "=" * 50)
