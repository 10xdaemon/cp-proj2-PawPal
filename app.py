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
preferred_categories = st.multiselect("Preferred categories", ["walk", "feeding", "medication", "grooming", "enrichment", "other"])


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

# BUG: Just as with the add task category. The other option in the dropdown for "species"
#.     should give the option to enter an arb species apart from cat and dog
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

# BUG: The counter for the table of task for a pet should start from 1 and not zero
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
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
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
                    time_of_day=time_of_day
                )
                selected_pet = next(p for p in st.session_state.owner.get_pets() if p.name == selected_pet_name)
                selected_pet.add_task(task)
                st.success(f"Task '{task.display_name}' added to {selected_pet_name}!")
            except ValueError as e:
                st.error(str(e))

    for pet in st.session_state.owner.get_pets():
        if pet.get_tasks():
            st.write(f"**{pet.name}'s tasks:**")
            st.dataframe(
                [
                    {
                        "Task": t.display_name,
                        "Category": t.category,
                        "Duration (min)": t.duration,
                        "Priority": t.priority,
                        "Frequency": t.frequency,
                        "Time": t.time_of_day if t.time_of_day else "any"
                    }
                    for i, t in enumerate(pet.get_tasks(), start=1)
                ],
                hide_index=True,
            )

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
                st.write(f"- [{t.priority.upper()}] **{t.display_name}** — {t.duration} min | {t.category} | {time_str}")

            if scheduler.skipped_tasks:
                st.write("**Skipped Tasks:**")
                for t in scheduler.skipped_tasks:
                    st.write(f"- {t.display_name} — {t.duration} min (not enough time)")

            st.info(f"**Reasoning:** {scheduler.reasoning}")
