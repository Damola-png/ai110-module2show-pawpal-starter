import streamlit as st

from pawpal_system import CareTask, OwnerProfile, PawPalSystem, PetProfile, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Plan and prioritize your pet care tasks with an OOP-powered scheduling engine.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner + Pet")
owner_name = st.text_input("Owner name", value="Jordan")
daily_budget = st.number_input("Daily available minutes", min_value=10, max_value=600, value=60)
preferred_times = st.multiselect(
    "Preferred task windows",
    ["morning", "afternoon", "evening", "anytime"],
    default=["morning", "evening"],
)

pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add tasks, then generate an optimized daily plan.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.selectbox(
        "Task type",
        ["walk", "feeding", "medication", "enrichment", "grooming", "vet_appointment"],
        index=0,
    )
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    due_window = st.selectbox("Due window", ["anytime", "morning", "afternoon", "evening"], index=1)

priority_map = {"low": 2, "medium": 3, "high": 5}

if st.button("Add task"):
    task_id = f"task_{len(st.session_state.tasks) + 1}"
    st.session_state.tasks.append(
        {
            "task_id": task_id,
            "task_type": task_title,
            "duration_minutes": int(duration),
            "priority": priority_map[priority_label],
            "due_window": due_window,
        }
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generates a plan based on priority, due windows, and your time budget.")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = OwnerProfile(
            owner_name=owner_name,
            daily_available_minutes=int(daily_budget),
            preferred_task_times=preferred_times,
        )
        pet = PetProfile(pet_name=pet_name, species=species)
        scheduler = Scheduler(priority_weights={"medication": 8, "vet_appointment": 8, "feeding": 5, "walk": 3})
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
                )
            )

        plan = system.generate_daily_plan(pet_name)
        explanations = scheduler.get_last_explanations()

        if not plan:
            st.info("No tasks fit within the current daily time budget.")
        else:
            st.success(f"Generated plan with {len(plan)} task(s).")
            st.table(
                [
                    {
                        "task_type": task.task_type,
                        "duration_minutes": task.duration_minutes,
                        "priority": task.priority,
                        "due_window": task.due_window,
                    }
                    for task in plan
                ]
            )
            st.markdown("### Why these tasks were selected")
            for task in plan:
                st.markdown(f"- {explanations.get(task.task_id, 'No explanation available')}")
