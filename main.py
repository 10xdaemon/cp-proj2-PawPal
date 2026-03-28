from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler


# --- Owner ---
owner = Owner(
    name="Jordan",
    available_minutes=90,
    preferred_time="morning",
    preferred_categories=["walk", "feeding"],
    avoid_categories=["grooming"]
)

# --- Pets ---
biscuit = Pet(name="Biscuit", species="dog", age=3, breed="Labrador")
mochi = Pet(name="Mochi", species="cat", age=5, breed="Siamese")

# --- Tasks for Biscuit ---
biscuit.add_task(Task(name="Morning Walk",  category="walk",       duration=30, priority="high",   time_of_day="morning"))
biscuit.add_task(Task(name="Breakfast",     category="feeding",    duration=10, priority="high",   time_of_day="morning"))
biscuit.add_task(Task(name="Bath Time",     category="grooming",   duration=20, priority="low",    time_of_day="afternoon"))

# --- Tasks for Mochi ---
mochi.add_task(Task(name="Feeding",         category="feeding",    duration=10, priority="high",   time_of_day="morning"))
mochi.add_task(Task(name="Playtime",        category="enrichment", duration=15, priority="medium",  time_of_day="afternoon"))
mochi.add_task(Task(name="Brush Fur",       category="grooming",   duration=10, priority="low",    time_of_day="evening"))

# --- Add pets to owner ---
owner.add_pet(biscuit)
owner.add_pet(mochi)

# --- Schedule & Display ---
print("=" * 45)
print("           TODAY'S SCHEDULE")
print("=" * 45)

for pet in owner.get_pets():
    scheduler = Scheduler(owner=owner, pet=pet, date=date.today())
    scheduler.generate_plan()
    scheduler.display()
    print()
