import streamlit as st
import pandas as pd
from datetime import date, time as dt_time
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+ Demo", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# -------------------------
# Demo Seed (runs once)
# -------------------------
# Builds a rich scenario with two pets:
#   Biscuit (dog) — 4 scheduled, 1 conflict, 1 low-priority skipped
#   Luna    (cat) — all tasks fit cleanly, no conflicts
#
# Schedule for Biscuit is pre-generated so every output section
# (metrics, conflict warning, task table, skipped expander, reasoning)
# is visible immediately on load.

if "demo_seeded" not in st.session_state:
    owner = Owner(
        name="Alex",
        available_minutes=75,
        preferred_time="morning",
        preferred_categories=["walk", "medication"],
    )

    # --- Biscuit ---
    biscuit = Pet(name="Biscuit", species="dog", age=3, breed="Labrador")
    # Morning Walk ends 08:30; Feeding starts 08:15 → intentional conflict
    biscuit.add_task(Task(name="Morning Walk", category="walk",       duration=30, priority="high",   frequency="daily",  time_of_day="08:00"))
    biscuit.add_task(Task(name="Feeding",      category="feeding",    duration=10, priority="high",   frequency="daily",  time_of_day="08:15"))
    biscuit.add_task(Task(name="Medication",   category="medication", duration=5,  priority="high",   frequency="daily",  time_of_day="09:00"))
    biscuit.add_task(Task(name="Evening Walk", category="walk",       duration=25, priority="medium", frequency="daily",  time_of_day="18:00"))
    # Bath Time is low-priority and won't fit in the 5 min remaining after the above 4 tasks (70 min used of 75)
    biscuit.add_task(Task(name="Bath Time",    category="grooming",   duration=45, priority="low",    frequency="daily",  time_of_day=""))

    # --- Luna ---
    luna = Pet(name="Luna", species="cat", age=2, breed="Tabby")
    luna.add_task(Task(name="Morning Feeding",   category="feeding",    duration=10, priority="high",   frequency="daily",  time_of_day="07:30"))
    luna.add_task(Task(name="Evening Feeding",   category="feeding",    duration=10, priority="high",   frequency="daily",  time_of_day="18:00"))
    luna.add_task(Task(name="Afternoon Playtime",category="enrichment", duration=20, priority="medium", frequency="daily",  time_of_day="14:00"))
    luna.add_task(Task(name="Brush Fur",         category="grooming",   duration=15, priority="low",    frequency="daily",  time_of_day=""))

    owner.add_pet(biscuit)
    owner.add_pet(luna)

    # Pre-generate schedule for Biscuit
    scheduler = Scheduler(owner=owner, pet=biscuit, date=date.today())
    scheduler.generate_plan()

    st.session_state.owner     = owner
    st.session_state.scheduler = scheduler
    st.session_state.demo_seeded = True

# -------------------------
# Owner Setup
# -------------------------
st.subheader("Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Alex")
with col2:
    available_minutes = st.number_input("Available time (min/day)", min_value=10, max_value=480, value=75)

preferred_time = st.selectbox("Preferred time of day", ["any", "morning", "afternoon", "evening"], index=1)
preferred_categories = st.multiselect(
    "Preferred categories",
    ["walk", "feeding", "medication", "grooming", "enrichment", "other"],
    default=["walk", "medication"],
)

if st.button("Save Owner"):
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferred_time=preferred_time,
        preferred_categories=preferred_categories,
    )
    st.success(f"Owner '{owner_name}' saved!")

st.divider()

# -------------------------
# Add a Pet
# -------------------------
if st.session_state.owner:
    st.subheader("Add a Pet")

    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name")
        age = st.number_input("Age", min_value=0, max_value=30, value=1)
    with col2:
        species_choice = st.selectbox("Species", ["dog", "cat", "other"])
        if species_choice == "other":
            species = st.text_input("Species name")
        else:
            species = species_choice
        breed = st.text_input("Breed")

    if st.button("Add Pet"):
        if species_choice == "other" and not species:
            st.warning("Please enter a species name.")
        elif pet_name:
            try:
                pet = Pet(name=pet_name, species=species, age=int(age), breed=breed)
                st.session_state.owner.add_pet(pet)
                st.success(f"{pet_name} added!")
            except ValueError as e:
                st.error(str(e))
        else:
            st.warning("Please enter a pet name.")

    if st.session_state.owner.get_pets():
        st.write("**Your Pets:**")
        for p in st.session_state.owner.get_pets():
            st.write(f"- {p.name} ({p.species}, age {p.age})")

st.divider()

# -------------------------
# Add a Task
# -------------------------
if st.session_state.owner and st.session_state.owner.get_pets():
    st.subheader("Add a Task")

    pet_names = [p.name for p in st.session_state.owner.get_pets()]
    selected_pet_name = st.selectbox("Assign to pet", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])
        if category == "other":
            custom_name = st.text_input("Task name")
        else:
            custom_name = ""
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
        flexible = st.checkbox("Flexible time (any)", value=True)
        if not flexible:
            task_time = st.time_input("Preferred time (HH:MM)", value=dt_time(8, 0))
            time_of_day = task_time.strftime("%H:%M")
        else:
            time_of_day = ""

    if st.button("Add Task"):
        if category == "other" and not custom_name:
            st.warning("Please enter a name for the custom task.")
        else:
            try:
                task = Task(
                    category=category,
                    duration=int(duration),
                    priority=priority,
                    name=custom_name,
                    frequency=frequency,
                    time_of_day=time_of_day,
                )
                selected_pet = next(p for p in st.session_state.owner.get_pets() if p.name == selected_pet_name)
                selected_pet.add_task(task)
                st.success(f"Task '{task.display_name}' added to {selected_pet_name}!")
            except ValueError as e:
                st.error(str(e))

    for pet in st.session_state.owner.get_pets():
        if pet.get_tasks():
            st.write(f"**{pet.name}'s tasks:**")
            tasks = pet.get_tasks()
            df = pd.DataFrame(
                [
                    {
                        "Task": t.display_name,
                        "Duration (min)": t.duration,
                        "Priority": t.priority,
                        "Frequency": t.frequency,
                        "Time": t.time_of_day if t.time_of_day else "any",
                    }
                    for t in tasks
                ],
                index=range(1, len(tasks) + 1),
            )
            st.dataframe(df)

st.divider()

# -------------------------
# Generate Schedule
# -------------------------
if st.session_state.owner and st.session_state.owner.get_pets():
    st.subheader("Generate Schedule")

    pet_names = [p.name for p in st.session_state.owner.get_pets()]
    schedule_pet_name = st.selectbox("Schedule for", pet_names, key="schedule_pet")

    if st.button("Generate Schedule"):
        selected_pet = next(p for p in st.session_state.owner.get_pets() if p.name == schedule_pet_name)
        if not selected_pet.get_tasks():
            st.warning(f"{schedule_pet_name} has no tasks. Add some above first.")
        else:
            scheduler = Scheduler(owner=st.session_state.owner, pet=selected_pet, date=date.today())
            scheduler.generate_plan()
            st.session_state.scheduler = scheduler

    if st.session_state.scheduler:
        scheduler = st.session_state.scheduler

        # At-a-glance metrics
        total_time = sum(t.duration for t in scheduler.scheduled_tasks)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tasks Scheduled", len(scheduler.scheduled_tasks))
        with col2:
            st.metric("Time Committed", f"{total_time} min")
        with col3:
            st.metric("Tasks Skipped", len(scheduler.skipped_tasks))

        # Conflicts — shown before the table so the owner sees them immediately
        if scheduler.conflicts:
            st.error(
                f"**{len(scheduler.conflicts)} time conflict(s) detected** — "
                "Two or more tasks overlap. Edit a task's start time or duration to resolve."
            )
            for w in scheduler.conflicts:
                st.write(w)
        else:
            st.success("No scheduling conflicts detected.")

        # Scheduled tasks table — already sorted chronologically by generate_plan
        st.write("**Scheduled Tasks:**")
        if scheduler.scheduled_tasks:
            st.dataframe(
                [
                    {
                        "Time": t.time_of_day if t.time_of_day else "flexible",
                        "Task": t.display_name,
                        "Duration (min)": t.duration,
                        "Priority": t.priority.upper(),
                    }
                    for t in scheduler.scheduled_tasks
                ],
                hide_index=True,
            )
        else:
            st.warning("No tasks could be scheduled. Try increasing your available time or adding tasks.")

        # Skipped tasks collapsed by default — secondary info
        if scheduler.skipped_tasks:
            with st.expander(f"Skipped Tasks ({len(scheduler.skipped_tasks)}) — not enough time"):
                st.dataframe(
                    [
                        {
                            "Task": t.display_name,
                            "Duration (min)": t.duration,
                            "Priority": t.priority.upper(),
                        }
                        for t in scheduler.skipped_tasks
                    ],
                    hide_index=True,
                )
                st.caption(
                    "Increase your available time or remove lower-priority tasks to fit these in."
                )

        st.write("**Plan**")
        st.info(scheduler.reasoning)
