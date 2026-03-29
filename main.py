from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler

# --- Setup ---
owner = OwnerProfile(
    owner_name="Jordan",
    daily_available_minutes=120,
    preferred_task_times=["morning"],
)

mochi = PetProfile(pet_name="Mochi", species="dog", energy_level="high", age=3)
luna  = PetProfile(pet_name="Luna",  species="cat", age=11, medical_notes="joint supplement")

scheduler = Scheduler(priority_weights={"medication": 10, "walk": 3, "feeding": 2})
system    = PawPalSystem(owner=owner, pets=[mochi, luna], scheduler=scheduler)

# --- Tasks added OUT OF ORDER (scheduled_time is intentionally shuffled) ---
system.add_task(CareTask("mochi-enrichment",  "Mochi", "enrichment",  20, priority=3,
                          due_window="afternoon", scheduled_time="14:00"))
system.add_task(CareTask("luna-litter",       "Luna",  "litter",      10, priority=3,
                          due_window="anytime",   scheduled_time="19:30"))
system.add_task(CareTask("mochi-walk",        "Mochi", "walk",        30, priority=4,
                          due_window="morning",   scheduled_time="07:30"))
system.add_task(CareTask("luna-medication",   "Luna",  "medication",   5, priority=5,
                          due_window="morning",   scheduled_time="08:00"))
system.add_task(CareTask("mochi-feed-am",     "Mochi", "feeding",     10, priority=5,
                          due_window="morning",   scheduled_time="08:30"))
system.add_task(CareTask("luna-feed-am",      "Luna",  "feeding",     10, priority=5,
                          due_window="morning",   scheduled_time="08:30"))
system.add_task(CareTask("mochi-grooming",    "Mochi", "grooming",    15, priority=2,
                          due_window="afternoon", scheduled_time="15:00",
                          recurrence="weekly", scheduled_weekday=5))  # Saturdays
system.add_task(CareTask("luna-vet-checkup",  "Luna",  "vet_appointment", 45, priority=5,
                          due_window="morning",   scheduled_time="10:00",
                          recurrence="weekly", scheduled_weekday=1))  # Tuesdays

# --- Intentional time conflicts to trigger detect_time_conflicts() ---
# Both Mochi's walk and Luna's medication are at 08:00 (same-time, different pets)
# Mochi's grooming and enrichment are both at 14:00 (same-time, same pet)
system.add_task(CareTask("mochi-grooming-extra", "Mochi", "grooming",   10, priority=2,
                          due_window="afternoon", scheduled_time="14:00"))
system.tasks[2].scheduled_time = "08:00"   # move mochi-walk to 08:00 (clashes with luna-medication)

# --- Mark mochi-walk as already done before generating the plan ---
system.filter_tasks(pet_name="Mochi", status="pending")[0].mark_complete()

TODAY_WEEKDAY = 5  # Saturday

# ─── 0. TIME CONFLICT DETECTION ─────────────────────────────────────────────
print("=" * 54)
print("   DEMO 0: detect_time_conflicts()  (warnings only)")
print("=" * 54)
conflict_warnings = scheduler.detect_time_conflicts(system.tasks)
if conflict_warnings:
    for w in conflict_warnings:
        print(f"\n  [!] {w}")
else:
    print("\n  No time conflicts detected.")

# ─── 1. SORT BY TIME DEMO ────────────────────────────────────────────────────
print("=" * 54)
print("   DEMO 1: sort_by_time()  (added out of order)")
print("=" * 54)
all_tasks = system.tasks
sorted_tasks = scheduler.sort_by_time(all_tasks)
print(f"\n  {'TIME':<8}  {'PET':<8}  {'TYPE':<18}  STATUS")
print(f"  {'-' * 48}")
for t in sorted_tasks:
    time_label = t.scheduled_time if t.scheduled_time else "--:--"
    print(f"  {time_label:<8}  {t.pet_name:<8}  {t.task_type:<18}  {t.status}")

# ─── 2. FILTER BY STATUS DEMO ────────────────────────────────────────────────
print("\n" + "=" * 54)
print("   DEMO 2: filter_tasks() by status")
print("=" * 54)
for label in ("complete", "pending", "skipped"):
    matches = system.filter_tasks(status=label)
    ids = ", ".join(t.task_id for t in matches) or "none"
    print(f"\n  {label.upper():<10}  {ids}")

# ─── 3. FILTER BY PET NAME DEMO ──────────────────────────────────────────────
print("\n" + "=" * 54)
print("   DEMO 3: filter_tasks() by pet name")
print("=" * 54)
for pet in system.pets:
    pet_tasks = system.filter_tasks(pet_name=pet.pet_name)
    print(f"\n  {pet.pet_name} ({len(pet_tasks)} tasks):")
    for t in scheduler.sort_by_time(pet_tasks):
        time_label = t.scheduled_time if t.scheduled_time else "--:--"
        print(f"    {time_label}  {t.task_type:<18}  [{t.status}]")

# ─── 4. FULL DAILY SCHEDULE (sorted by time window then HH:MM) ───────────────
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def print_schedule(pet_name: str) -> None:
    plan         = system.generate_daily_plan(pet_name, weekday=TODAY_WEEKDAY)
    explanations = scheduler.get_last_explanations()
    conflicts    = scheduler.get_last_conflicts()
    sorted_plan  = scheduler.sort_by_time(plan)
    total        = sum(t.duration_minutes for t in sorted_plan)

    print(f"\n  {pet_name}'s Schedule")
    print(f"  {'-' * 48}")
    if conflicts:
        for w in conflicts:
            print(f"  [!] {w}")
        print()
    if not sorted_plan:
        print("  No tasks scheduled today.")
    else:
        for t in sorted_plan:
            time_label = t.scheduled_time if t.scheduled_time else "--:--"
            recur = f"({t.recurrence})".ljust(10)
            print(f"  {time_label}  [{t.due_window:<10}]  {recur}  {t.task_type:<18}  {t.duration_minutes:>3} min  (p{t.priority})")
            print(f"         > {explanations.get(t.task_id, '')}")
    print(f"\n  Total: {total} min / {owner.daily_available_minutes} min")

print("\n" + "=" * 54)
print(f"   TODAY'S SCHEDULE  -  {DAYS[TODAY_WEEKDAY]}  |  Owner: {owner.owner_name}")
print("=" * 54)
for pet in system.pets:
    print_schedule(pet.pet_name)

print("\n" + "=" * 54)
