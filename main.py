from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, detect_cross_pet_conflicts


# --- Owner ---
owner = Owner(
    name="Jordan",
    available_minutes=90,
    preferred_time="morning",
    preferred_categories=["walk", "feeding"],
)

# --- Pets ---
biscuit = Pet(name="Biscuit", species="dog", age=3, breed="Labrador")
mochi   = Pet(name="Mochi",   species="cat", age=5, breed="Siamese")

# --- Tasks for Biscuit (added OUT OF ORDER intentionally) ---
biscuit.add_task(Task(name="Evening Walk",  category="walk",       duration=25, priority="medium", frequency="daily",  time_of_day="18:00"))
biscuit.add_task(Task(name="Breakfast",     category="feeding",    duration=10, priority="high",   frequency="daily",  time_of_day="07:30"))
biscuit.add_task(Task(name="Bath Time",     category="grooming",   duration=20, priority="low",    frequency="weekly", time_of_day="11:00"))
biscuit.add_task(Task(name="Morning Walk",  category="walk",       duration=30, priority="high",   frequency="daily",  time_of_day="08:00"))
biscuit.add_task(Task(name="Medication",    category="medication", duration=5,  priority="high",   frequency="daily",  time_of_day=""))

# Mark one task complete to test completion filtering
biscuit.tasks[1].mark_complete()   # Breakfast is already done

# --- Tasks for Mochi (added OUT OF ORDER intentionally) ---
mochi.add_task(Task(name="Afternoon Play",  category="enrichment", duration=15, priority="medium", frequency="daily",  time_of_day="14:00"))
mochi.add_task(Task(name="Feeding",         category="feeding",    duration=10, priority="high",   frequency="daily",  time_of_day="08:00"))
mochi.add_task(Task(name="Brush Fur",       category="grooming",   duration=10, priority="low",    frequency="weekly", time_of_day="19:00"))
mochi.add_task(Task(name="Evening Feeding", category="feeding",    duration=10, priority="high",   frequency="daily",  time_of_day="18:30"))

# --- Add pets to owner ---
owner.add_pet(biscuit)
owner.add_pet(mochi)

# ─────────────────────────────────────────────
# 1. GENERATE & DISPLAY DAILY SCHEDULE
# ─────────────────────────────────────────────
print("=" * 50)
print("           TODAY'S SCHEDULE")
print("=" * 50)

for pet in owner.get_pets():
    scheduler = Scheduler(owner=owner, pet=pet, date=date.today())
    scheduler.generate_plan()
    scheduler.display()
    print()

# ─────────────────────────────────────────────
# 2. FILTER: all incomplete tasks across all pets
# ─────────────────────────────────────────────
print("=" * 50)
print("  INCOMPLETE TASKS (all pets)")
print("=" * 50)
for t in owner.filter_tasks(completed=False):
    print(f"  [ ] {t.display_name} ({t.category}, {t.time_of_day or 'any time'})")

print()

# ─────────────────────────────────────────────
# 3. FILTER: completed tasks across all pets
# ─────────────────────────────────────────────
print("=" * 50)
print("  COMPLETED TASKS (all pets)")
print("=" * 50)
for t in owner.filter_tasks(completed=True):
    print(f"  [x] {t.display_name} ({t.category})")

print()

# ─────────────────────────────────────────────
# 4. FILTER: all tasks for a specific pet
# ─────────────────────────────────────────────
print("=" * 50)
print("  ALL TASKS FOR BISCUIT")
print("=" * 50)
for t in owner.filter_tasks(pet_name="Biscuit"):
    status = "x" if t.is_completed else " "
    print(f"  [{status}] {t.display_name} — {t.time_of_day or 'any time'}")

print()

# ─────────────────────────────────────────────
# 5. SORT: Biscuit's raw tasks sorted by time
# ─────────────────────────────────────────────
print("=" * 50)
print("  BISCUIT'S TASKS SORTED BY TIME (raw)")
print("=" * 50)
scheduler_b = Scheduler(owner=owner, pet=biscuit, date=date.today())
for t in scheduler_b.sort_by_time(biscuit.get_tasks()):
    print(f"  {t.time_of_day or 'any time':>8}  {t.display_name}")

print()

# ─────────────────────────────────────────────
# 6. AUTO-RESCHEDULE on completion
# ─────────────────────────────────────────────
print("=" * 50)
print("  AUTO-RESCHEDULE DEMO")
print("=" * 50)

today = date.today()
tomorrow = today + timedelta(days=1)

biscuit.complete_task("Morning Walk", today)
mochi.complete_task("Feeding", today)

print(f"\nAfter completing 'Morning Walk' (daily) for Biscuit on {today}:")
for t in biscuit.get_tasks():
    status = "DONE" if t.is_completed else f"due {t.due_date or 'daily'}"
    print(f"  {t.display_name:20s}  [{status}]")

print(f"\nAfter completing 'Feeding' (daily) for Mochi on {today}:")
for t in mochi.get_tasks():
    status = "DONE" if t.is_completed else f"due {t.due_date or 'daily'}"
    print(f"  {t.display_name:20s}  [{status}]")

print(f"\nBiscuit's schedule for TOMORROW ({tomorrow}):")
sched_tomorrow = Scheduler(owner=owner, pet=biscuit, date=tomorrow)
sched_tomorrow.generate_plan()
if sched_tomorrow.scheduled_tasks:
    for t in sched_tomorrow.scheduled_tasks:
        print(f"  {t.time_of_day or 'any time':>8}  [{t.priority.upper()}] {t.display_name}")
else:
    print("  (no tasks scheduled)")

print()

# ─────────────────────────────────────────────
# 7. CONFLICT DETECTION (same pet)
# ─────────────────────────────────────────────
print("=" * 50)
print("  SAME-PET CONFLICT DETECTION")
print("=" * 50)

conflict_pet = Pet(name="Rex", species="dog", age=2, breed="Beagle")
# Intentional overlap: Vet Visit starts at 09:00 (60 min) → ends 10:00
#                      Grooming starts at 09:30 (45 min)  → overlaps 09:30–10:00
conflict_pet.add_task(Task(name="Vet Visit",  category="medication", duration=60, priority="high",   time_of_day="09:00"))
conflict_pet.add_task(Task(name="Grooming",   category="grooming",   duration=45, priority="medium", time_of_day="09:30"))
conflict_pet.add_task(Task(name="Lunch Feed", category="feeding",    duration=10, priority="high",   time_of_day="12:00"))

owner2 = Owner(name="Jordan", available_minutes=180)
owner2.add_pet(conflict_pet)
sched_conflict = Scheduler(owner=owner2, pet=conflict_pet, date=date.today())
sched_conflict.generate_plan()

if sched_conflict.conflicts:
    for w in sched_conflict.conflicts:
        print(w)
else:
    print("  No conflicts found.")

print()

# ─────────────────────────────────────────────
# 8. CONFLICT DETECTION (cross-pet)
# ─────────────────────────────────────────────
print("=" * 50)
print("  CROSS-PET CONFLICT DETECTION")
print("=" * 50)

cross_owner = Owner(name="Jordan", available_minutes=180)
dog = Pet(name="Buddy", species="dog", age=4, breed="Poodle")
cat = Pet(name="Luna",  species="cat", age=2, breed="Tabby")

dog.add_task(Task(name="Evening Walk",    category="walk",       duration=25, priority="high",   time_of_day="18:00"))
dog.add_task(Task(name="Morning Feed",    category="feeding",    duration=10, priority="high",   time_of_day="07:00"))
cat.add_task(Task(name="Evening Feeding", category="feeding",    duration=10, priority="high",   time_of_day="18:10"))  # overlaps dog walk
cat.add_task(Task(name="Morning Play",    category="enrichment", duration=15, priority="medium", time_of_day="09:00"))

cross_owner.add_pet(dog)
cross_owner.add_pet(cat)

sched_dog = Scheduler(owner=cross_owner, pet=dog, date=date.today())
sched_cat = Scheduler(owner=cross_owner, pet=cat, date=date.today())
sched_dog.generate_plan()
sched_cat.generate_plan()

cross_warnings = detect_cross_pet_conflicts([sched_dog, sched_cat])
if cross_warnings:
    for w in cross_warnings:
        print(w)
else:
    print("  No cross-pet conflicts found.")

print()

# ─────────────────────────────────────────────
# 9. LOW-PRIORITY SKIPPING (verbose reasoning)
# ─────────────────────────────────────────────
print("=" * 50)
print("  LOW-PRIORITY TASK SKIPPING")
print("=" * 50)

daisy = Pet(name="Daisy", species="dog", age=2, breed="Beagle")
daisy.add_task(Task(name="Morning Walk", category="walk",       duration=30, priority="high", frequency="daily", time_of_day="08:00"))
daisy.add_task(Task(name="Medication",  category="medication", duration=10, priority="high", frequency="daily", time_of_day="09:00"))
daisy.add_task(Task(name="Playtime",    category="enrichment", duration=20, priority="low",  frequency="daily", time_of_day=""))
daisy.add_task(Task(name="Nail Trim",   category="grooming",   duration=15, priority="low",  frequency="daily", time_of_day=""))

# 45 min available — high-priority tasks use 40 min, leaving only 5 min
# which is not enough for either low-priority task (20 and 15 min)
tight_owner = Owner(name="Jordan", available_minutes=45)
tight_owner.add_pet(daisy)

tight_sched = Scheduler(owner=tight_owner, pet=daisy, date=date.today())
tight_sched.generate_plan()
tight_sched.display()
