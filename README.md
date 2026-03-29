# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smart Scheduling

PawPal+ goes beyond a basic task list with several scheduling intelligence features built into `pawpal_system.py`.

### Urgency-Based Priority
Tasks are ranked by a numeric urgency score that combines **priority** (high/medium/low) and **frequency** (daily/weekly/as_needed). A high-priority daily task always outranks a low-priority weekly one. Within equal urgency, preferred-category tasks are promoted and shorter tasks are scheduled first as a tie-breaker.

### HH:MM Time Ordering
Tasks accept a specific `time_of_day` in `HH:MM` format (e.g. `"08:30"`). After the schedule is built, tasks are automatically reordered chronologically so the owner sees a real timeline. Tasks with no fixed time are placed at the end.

### Auto-Rescheduling on Completion
When a task is marked complete via `Pet.complete_task()`, a new instance is automatically created for the next occurrence — tomorrow for daily tasks, 7 days later for weekly tasks. The completed record is preserved as history. `as_needed` tasks are marked done with no auto-reschedule.

### Frequency-Aware Filtering
The scheduler respects task frequency when building the daily plan. Weekly tasks only appear on Mondays. `as_needed` tasks are excluded from automatic scheduling entirely. Future-dated rescheduled instances are hidden until their due date arrives.

### Conflict Detection
Two layers of conflict detection surface time overlaps as warning messages without crashing the app:
- **Same-pet** — `Scheduler.detect_conflicts()` checks whether any two scheduled tasks for the same pet overlap in time. Called automatically after every `generate_plan()`.
- **Cross-pet** — `detect_cross_pet_conflicts(schedulers)` compares tasks across different pets to catch cases where the owner would be double-booked.

## Testing PawPal+

The following command was used to test the code.

```bash
cd tests
python -m pytest
```

### What the tests cover

- **Task basics** — marking a task complete flips `is_completed`; adding tasks increases the pet's task count
- **`Task.display_name`** — falls back to category when name is empty; respects explicit names and `"other"` category
- **`Task.reschedule`** — daily tasks reschedule +1 day, weekly +7 days, `as_needed` returns `None`; rescheduled tasks start incomplete and preserve all original attributes
- **`Pet.get_tasks`** — returns an empty list by default and the correct tasks after adds
- **`Pet.add_task` duplicate detection** — raises `ValueError` when the same category + due date is added twice; allows the same category on different dates
- **`Pet.complete_task`** — marks the task done, auto-appends a rescheduled instance for daily/weekly tasks, skips rescheduling for `as_needed`, raises on unknown or already-completed tasks
- **`Scheduler.generate_plan`** — respects time budget (fits tasks, skips overflows); schedules by priority (high before low); excludes avoided categories, completed tasks, and `as_needed` tasks; sorts output chronologically; promotes preferred categories
- **`Scheduler.explain_reasoning`** — output includes the pet's name, scheduled count, skipped notice when tasks are dropped, and references to preferred/avoided categories
- **`Scheduler.urgency_score`** — high > medium > low priority; daily > weekly frequency; spot-checks expected numeric values (120 for high/daily, 10 for low/as_needed)
- **`Scheduler.sort_by_time`** — chronological ordering, flexible (no time) tasks placed last, input list not mutated
- **Conflict detection (same-pet)** — no conflict for non-overlapping or back-to-back tasks; flags partial overlaps, same-start-time, fully contained tasks, 1-minute overlaps, and three-way overlaps; conflict messages name both tasks; `sched.conflicts` populated after `generate_plan()`
- **Cross-pet conflict detection** — `detect_cross_pet_conflicts()` clears non-overlapping schedules, flags overlapping windows across pets, ignores flexible (untimed) tasks
- **`Owner.filter_tasks`** — no filter returns all tasks; filters by pet name, completion status, or both combined; unknown pet name returns empty list
- **`Owner.add_pet` duplicate guard** — raises `ValueError` on duplicate pet names; allows different names

### Confidence Level

★★★★★ — All **77 tests pass**. 
Core scheduling logic:
1. Priority ranking
1. Time budgeting 
1. Recurrence
1. Conflict detection 
1. Filtering
1. Sorting; were thoroughly covered with both happy-path and edge cases.