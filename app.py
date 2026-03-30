import streamlit as st

from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan and prioritize your pet care tasks with a smart scheduling engine.")


def _priority_badge(priority: int) -> str:
    if priority >= 5:
        return "🔴 High"
    if priority >= 3:
        return "🟡 Medium"
    return "🟢 Low"


def _persist_data() -> None:
    owner = OwnerProfile(
        owner_name=st.session_state.owner_name,
        daily_available_minutes=int(st.session_state.daily_budget),
        preferred_task_times=list(st.session_state.preferred_times),
    )
    pet = PetProfile(
        pet_name=st.session_state.pet_name,
        species=st.session_state.species,
    )
    tasks = [
        CareTask(
            task_id=row["task_id"],
            pet_name=st.session_state.pet_name,
            task_type=row["task_type"],
            duration_minutes=row["duration_minutes"],
            priority=row["priority"],
            due_window=row["due_window"],
            scheduled_time=row["scheduled_time"],
        )
        for row in st.session_state.tasks
    ]
    owner.save_to_json([pet], tasks)


if "persistence_loaded" not in st.session_state:
    loaded_owner, loaded_pets, loaded_tasks = OwnerProfile.load_from_json()
    loaded_pet = loaded_pets[0] if loaded_pets else PetProfile(pet_name="Mochi", species="dog")

    st.session_state.owner_name = loaded_owner.owner_name
    st.session_state.daily_budget = loaded_owner.daily_available_minutes
    st.session_state.preferred_times = loaded_owner.preferred_task_times or ["morning"]

    st.session_state.pet_name = loaded_pet.pet_name
    st.session_state.species = loaded_pet.species if loaded_pet.species in {"dog", "cat", "other"} else "other"

    st.session_state.tasks = [
        {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "duration_minutes": task.duration_minutes,
            "priority": task.priority,
            "due_window": task.due_window,
            "scheduled_time": task.scheduled_time,
        }
        for task in loaded_tasks
    ]
    st.session_state.persistence_loaded = True

st.divider()

# ── 1. Owner + Pet ────────────────────────────────────────────────────────────
st.subheader("Owner & Pet")
col_a, col_b = st.columns(2)
with col_a:
    owner_name = st.text_input("Owner name", key="owner_name")
    daily_budget = st.number_input(
        "Daily available minutes", min_value=10, max_value=600, key="daily_budget"
    )
    preferred_times = st.multiselect(
        "Preferred task windows",
        ["morning", "afternoon", "evening", "anytime"],
        key="preferred_times",
    )
with col_b:
    pet_name = st.text_input("Pet name", key="pet_name")
    species = st.selectbox("Species", ["dog", "cat", "other"], key="species")

st.divider()

# ── 2. Add tasks ──────────────────────────────────────────────────────────────
st.subheader("Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_type = st.selectbox(
        "Task type",
        ["walk", "feeding", "medication", "enrichment", "grooming", "vet_appointment"],
    )
    due_window = st.selectbox(
        "Due window", ["morning", "afternoon", "evening", "anytime"], index=0
    )
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col3:
    scheduled_time = st.text_input(
        "Start time (HH:MM, optional)", value="", placeholder="e.g. 08:30"
    )

priority_map = {"low": 2, "medium": 3, "high": 5}

if st.button("Add task", type="primary"):
    # Validate HH:MM if provided
    time_error = None
    if scheduled_time.strip():
        parts = scheduled_time.strip().split(":")
        if (
            len(parts) != 2
            or not parts[0].isdigit()
            or not parts[1].isdigit()
            or not (0 <= int(parts[0]) <= 23)
            or not (0 <= int(parts[1]) <= 59)
        ):
            time_error = "Start time must be in HH:MM format (e.g. 08:30)."

    if time_error:
        st.error(time_error)
    else:
        st.session_state.tasks.append(
            {
                "task_id": f"task_{len(st.session_state.tasks) + 1}",
                "task_type": task_type,
                "duration_minutes": int(duration),
                "priority": priority_map[priority_label],
                "due_window": due_window,
                "scheduled_time": scheduled_time.strip(),
            }
        )
        _persist_data()
        st.success(f"Added: {task_type} ({duration} min, {due_window})")

# Current task list
if st.session_state.tasks:
    st.markdown("**Current tasks**")
    display_rows = [
        {
            "Type": t["task_type"],
            "Window": t["due_window"],
            "Start": t["scheduled_time"] if t["scheduled_time"] else "--:--",
            "Duration": f"{t['duration_minutes']} min",
            "Priority": _priority_badge(t["priority"]),
        }
        for t in st.session_state.tasks
    ]
    st.table(display_rows)

    if st.button("Clear all tasks"):
        st.session_state.tasks = []
        _persist_data()
        st.rerun()
else:
    st.info("No tasks yet — add one above.")

st.divider()

# ── 3. Generate schedule ──────────────────────────────────────────────────────
st.subheader("Generate Schedule")
st.caption("Sorts by start time, respects your budget, and flags any conflicts.")

if st.button("Generate schedule", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = OwnerProfile(
            owner_name=owner_name,
            daily_available_minutes=int(daily_budget),
            preferred_task_times=preferred_times,
        )
        pet = PetProfile(pet_name=pet_name, species=species)
        scheduler = Scheduler(
            priority_weights={
                "medication": 8,
                "vet_appointment": 8,
                "feeding": 5,
                "walk": 3,
            }
        )
        system = PawPalSystem(owner=owner, pets=[pet], scheduler=scheduler)

        for row in st.session_state.tasks:
            system.add_task(
                CareTask(
                    task_id=row["task_id"],
                    pet_name=pet_name,
                    task_type=row["task_type"],
                    duration_minutes=row["duration_minutes"],
                    priority=row["priority"],
                    due_window=row["due_window"],
                    scheduled_time=row["scheduled_time"],
                )
            )

        # ── conflict detection ────────────────────────────────────────────────
        time_conflicts = scheduler.detect_time_conflicts(system.tasks)
        if time_conflicts:
            st.markdown("#### ⚠️ Scheduling Conflicts Detected")
            for warning in time_conflicts:
                # Strip the leading "WARNING: " prefix for a cleaner UI message
                msg = warning.replace("WARNING: ", "")
                st.warning(f"**Time conflict:** {msg}")
            st.caption(
                "Tip: Edit your task start times above so no two tasks begin at the same time."
            )

        # ── generate + sort plan ──────────────────────────────────────────────
        plan = system.generate_daily_plan(pet_name)
        cross_window_conflicts = scheduler.get_last_conflicts()
        explanations = scheduler.get_last_explanations()

        task_by_id = {task.task_id: task for task in system.tasks}
        for row in st.session_state.tasks:
            updated = task_by_id.get(row["task_id"])
            if updated is not None:
                row["scheduled_time"] = updated.scheduled_time

        _persist_data()

        if cross_window_conflicts:
            for conflict in cross_window_conflicts:
                msg = conflict.replace("WARNING: ", "")
                st.warning(f"**Duplicate task type:** {msg}")

        if not plan:
            st.info("No tasks fit within the current daily time budget.")
        else:
            sorted_plan = scheduler.sort_by_priority_then_time(plan)
            used = sum(t.duration_minutes for t in sorted_plan)

            st.success(
                f"Plan ready — {len(sorted_plan)} task(s), "
                f"{used} / {daily_budget} minutes used."
            )

            # ── schedule table ────────────────────────────────────────────────
            st.markdown(f"#### {pet_name}'s Schedule for Today")
            st.table(
                [
                    {
                        "Start": t.scheduled_time if t.scheduled_time else "--:--",
                        "Window": t.due_window,
                        "Task": t.task_type,
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": _priority_badge(t.priority),
                        "Status": t.status,
                    }
                    for t in sorted_plan
                ]
            )

            # ── why each task was selected ────────────────────────────────────
            st.markdown("#### Why these tasks were selected")
            for task in sorted_plan:
                explanation = explanations.get(task.task_id, "")
                time_label = task.scheduled_time if task.scheduled_time else task.due_window
                st.success(f"**{time_label} — {task.task_type}:** {explanation}")

            # ── tasks left out ────────────────────────────────────────────────
            planned_ids = {t.task_id for t in sorted_plan}
            skipped = [
                t for t in system.tasks if t.task_id not in planned_ids
            ]
            if skipped:
                st.markdown("#### Tasks not scheduled (budget exceeded)")
                for t in skipped:
                    st.warning(
                        f"**{t.task_type}** ({t.duration_minutes} min, priority {t.priority}) "
                        f"— did not fit within the {daily_budget}-minute budget."
                    )
