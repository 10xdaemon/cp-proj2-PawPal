import streamlit as st
from datetime import date, time as dt_time
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session State Init ---
if "owner" not in st.session_state:
    st.session_state.owner = None

# -------------------------
# Owner Setup
# -------------------------
st.subheader("Owner Info")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available time (min/day)", min_value=10, max_value=480, value=90)

preferred_time = st.selectbox("Preferred time of day", ["any", "morning", "afternoon", "evening"])
preferred_categories = st.multiselect("Preferred categories", ["walk", "feeding", "medication", "grooming", "enrichment"])
avoid_categories = st.multiselect("Avoid categories", ["walk", "feeding", "medication", "grooming", "enrichment"])

if st.button("Save Owner"):
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferred_time=preferred_time,
        preferred_categories=preferred_categories,
        avoid_categories=avoid_categories
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
        species = st.selectbox("Species", ["dog", "cat", "other"])
        breed = st.text_input("Breed")

    if st.button("Add Pet"):
        if pet_name:
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
        task_name = st.text_input("Task name", value="Morning walk")
        category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
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
        if task_name:
            try:
                task = Task(
                    name=task_name,
                    category=category,
                    duration=int(duration),
                    priority=priority,
                    frequency=frequency,
                    time_of_day=time_of_day
                )
                selected_pet = next(p for p in st.session_state.owner.get_pets() if p.name == selected_pet_name)
                selected_pet.add_task(task)
                st.success(f"Task '{task_name}' added to {selected_pet_name}!")
            except ValueError as e:
                st.error(str(e))
        else:
            st.warning("Please enter a task name.")

    for pet in st.session_state.owner.get_pets():
        if pet.get_tasks():
            st.write(f"**{pet.name}'s tasks:**")
            st.table([
                {
                    "Task": t.name,
                    "Category": t.category,
                    "Duration (min)": t.duration,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Time": t.time_of_day if t.time_of_day else "any"
                }
                for t in pet.get_tasks()
            ])

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

            st.success(scheduler.get_summary())

            st.write("**Scheduled Tasks:**")
            for t in scheduler.scheduled_tasks:
                time_str = t.time_of_day if t.time_of_day else "any time"
                st.write(f"- [{t.priority.upper()}] **{t.name}** — {t.duration} min | {t.category} | {time_str}")

            if scheduler.skipped_tasks:
                st.write("**Skipped Tasks:**")
                for t in scheduler.skipped_tasks:
                    st.write(f"- {t.name} — {t.duration} min (not enough time)")

            st.info(f"**Reasoning:** {scheduler.reasoning}")
