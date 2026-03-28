# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
### Three core actions the user should be able to perform are
1. add a pet
2. a summary showing what should be done that day
3. shedule a service

### Potential Edge Cases
1. What if the owner has no time in that day?
2. More than 5 pets, scheduling complexity

- Briefly describe your initial UML design.
The initial design I kept it simple and follwed the reqs from the README closely. After the initial brainstorm with claude code
there was some clarity issuses for me, just understanding what the main objects would look like and how they connect. And so after some refining I came to understand that there's 4 main objects to the design.

- What classes did you include, and what responsibilities did you assign to each?
The 4 main classes are:
1. Owner
1. Pet
1. Task
1. Scheduler

**b. Design changes**

- Did your design change during implementation?
Yes it changed where at first there we're 6 main objects, the 4 mentioned before and plus 2: DailyPlan and Calendar. After 2/3 iterations it came back down to 4, eliminating the calendar entirely and aggregating DailyPlan and Scheduler.

- If yes, describe at least one change and why you made it.
So DailyPlan isn't independent of Scheduler. It's just the output of the Schedule so it was okay to fold its attributes in Schedle directly to produce a cleaner design. Also the preferences are a bit complex since there's so many scenarios to consider. 


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
*Answer*: I would add a calendar system to the app so that the user can have a general sense of what's happening during the week. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

---

## 6. Algorithm & Method Documentation

### `Task.reschedule(from_date)`
**Location:** `Task` class
**Purpose:** Creates the next occurrence of a recurring task after it is marked complete.
**How it works:** Looks up the task's `frequency` in an offset dict (`daily` → +1 day, `weekly` → +7 days). Returns a new `Task` instance with the same attributes and `due_date` set to the next occurrence. Returns `None` for `as_needed` tasks, which do not auto-recur.
**Tradeoff:** Weekly tasks always recur exactly 7 days later regardless of which day of the week the completion happened on.

---

### `Pet.complete_task(task_name, today)`
**Location:** `Pet` class
**Purpose:** Marks a task done and automatically queues the next instance.
**How it works:** Finds the first incomplete task matching `task_name`, calls `mark_complete()` on it, then calls `reschedule(today)`. If a next occurrence is returned, it is appended directly to `self.tasks` (bypassing the duplicate check since it has a different `due_date`).
**Tradeoff:** The completed record stays in the task list permanently. There is no archiving or cleanup of old completed instances.

---

### `Owner.filter_tasks(pet_name, completed)`
**Location:** `Owner` class
**Purpose:** Returns a filtered list of tasks across all pets, optionally narrowed by pet name and/or completion status.
**How it works:** If `pet_name` is provided, it narrows the pool to that pet's tasks only. If `completed` is `True` or `False`, it applies an equality filter on `task.is_completed`. Both parameters are optional and can be combined.
**Tradeoff:** Returns a flat list with no pet-name label attached, so the caller must track which pet each task belongs to if needed.

---

### `Scheduler.urgency_score(task)`
**Location:** `Scheduler` class
**Purpose:** Produces a single numeric rank for a task combining priority and frequency so both factors influence scheduling order.
**How it works:** Maps `priority` to a base score (high=100, medium=50, low=10) and adds a frequency boost (daily=20, weekly=5, as_needed=0). The sum is used as the primary sort key in `generate_plan`.
**Tradeoff:** The weights are fixed constants. A high-priority weekly task (105) outranks a medium daily task (70) even if the daily task is arguably more time-sensitive on a given day.

---

### `Scheduler.sort_by_time(tasks)`
**Location:** `Scheduler` class
**Purpose:** Orders a list of tasks chronologically by their `time_of_day` attribute for display purposes.
**How it works:** Uses the module-level `_task_window` helper to parse `"HH:MM"` into `(start_min, end_min)`. Tasks with no set time (`""`) receive `(inf, inf)` and sort to the end. Returns a new sorted list without mutating the input.
**Tradeoff:** Only affects display order. Tasks with the same start time have no further tie-breaking, so their relative order depends on Python's sort stability.

---

### `Scheduler.filter_tasks()`
**Location:** `Scheduler` class
**Purpose:** Narrows the pet's full task list down to only tasks that are valid candidates for today's schedule.
**How it works:** Applies five conditions in a single list comprehension — excludes avoided categories, completed tasks, `as_needed` tasks, weekly tasks on non-Monday days, and tasks whose `due_date` does not match today. Anything passing all five is returned.
**Tradeoff:** Weekly tasks are hardcoded to Mondays only. A more flexible design would let the owner choose which day of the week weekly tasks repeat on.

---

### `Scheduler.generate_plan()`
**Location:** `Scheduler` class
**Purpose:** Builds the owner's full daily schedule for one pet within the available time budget.
**How it works:** Calls `filter_tasks()` to get candidates, sorts them by `(-urgency_score, not_in_preferred_categories, duration)`, then iterates greedily — a task is scheduled if it fits in the remaining time, otherwise skipped. After packing, `sort_by_time` reorders the output chronologically and `detect_conflicts` runs automatically.
**Tradeoff:** Greedy first-fit means a large high-urgency task that narrowly doesn't fit is dropped in favor of smaller lower-urgency tasks. A knapsack approach would maximize total priority but adds algorithmic complexity.

---

### `Scheduler.detect_conflicts()`
**Location:** `Scheduler` class
**Purpose:** Identifies same-pet scheduling conflicts where two timed tasks overlap in time.
**How it works:** Collects all scheduled tasks that have a set `time_of_day`, then checks every pair using the overlap condition `a_start < b_end and b_start < a_end`. Warnings are stored in `self.conflicts` as plain strings. Never raises an exception — all issues are surfaced as messages.
**Tradeoff:** Only timed tasks are checked. Two flexible (`""`) tasks scheduled back-to-back could still cause a real-world conflict, but cannot be detected without an assumed start time.

---

### `detect_cross_pet_conflicts(schedulers)`
**Location:** Module-level function
**Purpose:** Detects time overlaps between tasks belonging to different pets — catching cases where the owner is double-booked across animals.
**How it works:** Collects `(start, end, task, pet_name)` tuples from all schedulers, then checks every cross-pet pair for overlap. Same-pet pairs are skipped since `detect_conflicts()` handles those. Returns a list of warning strings.
**Tradeoff:** Requires the caller to generate and pass all per-pet `Scheduler` instances manually. There is no automatic cross-pet check built into `generate_plan`.

---

### `_task_window(task)`
**Location:** Module-level helper
**Purpose:** Centralized parser that converts a task's `time_of_day` string into a numeric time window.
**How it works:** Splits `"HH:MM"` on `:`, converts to integers, and returns `(start_min, end_min)` where `end_min = start_min + task.duration`. Returns `None` for flexible tasks (`time_of_day == ""`). Shared by `sort_by_time`, `detect_conflicts`, and `detect_cross_pet_conflicts` to avoid duplicating parsing logic.
**Tradeoff:** Assumes `time_of_day` is always a valid `"HH:MM"` string if non-empty. Malformed input (e.g. `"8:5"`) would cause a runtime error.
