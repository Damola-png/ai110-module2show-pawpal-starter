import streamlit as st

from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan and prioritize your pet care tasks with a smart scheduling engine.")

st.divider()

# ── 1. Owner + Pet ────────────────────────────────────────────────────────────
st.subheader("Owner & Pet")
col_a, col_b = st.columns(2)
with col_a:
    owner_name = st.text_input("Owner name", value="Jordan")
    daily_budget = st.number_input(
        "Daily available minutes", min_value=10, max_value=600, value=90
    )
    preferred_times = st.multiselect(
        "Preferred task windows",
        ["morning", "afternoon", "evening", "anytime"],
        default=["morning"],
    )
with col_b:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

st.divider()

# ── 2. Add tasks ──────────────────────────────────────────────────────────────
st.subheader("Add a Task")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

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
            "Priority": t["priority"],
        }
        for t in st.session_state.tasks
    ]
    st.table(display_rows)

    if st.button("Clear all tasks"):
        st.session_state.tasks = []
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

        if cross_window_conflicts:
            for conflict in cross_window_conflicts:
                msg = conflict.replace("WARNING: ", "")
                st.warning(f"**Duplicate task type:** {msg}")

        if not plan:
            st.info("No tasks fit within the current daily time budget.")
        else:
            sorted_plan = scheduler.sort_by_time(plan)
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
                        "Priority": t.priority,
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
