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
