from dataclasses import dataclass, field
from datetime import date, timedelta

#TODO: 1. exclude task name and just keep the rename the categories as tasks and if it's anohter task 
#         choose "other" where they'll get the option to name the task.
@dataclass
class Task:
    name: str
    category: str        # walk / feeding / medication / grooming / enrichment
    duration: int        # minutes
    priority: str        # high / medium / low
    frequency: str = "daily"        # daily / weekly / as_needed
    time_of_day: str = ""           # HH:MM (e.g. "08:30"), or "" for flexible/any time
    is_completed: bool = False
    due_date: date | None = None    # None = template (every qualifying day); set = specific instance

    def mark_complete(self):
        """Mark this task as completed."""
        self.is_completed = True

    def mark_incomplete(self):
        """Reset this task to incomplete."""
        self.is_completed = False

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"

    def reschedule(self, from_date: date) -> "Task | None":
        """Return a new Task instance scheduled for the next occurrence after from_date.

        Computes the next due date based on the task's frequency:
          - daily  → from_date + 1 day
          - weekly → from_date + 7 days
          - as_needed → not rescheduled; returns None

        The new instance is a copy of this task with is_completed reset to False
        and due_date set to the computed next date. All other attributes are preserved.

        Args:
            from_date: The date the task was completed; next occurrence is relative to this.

        Returns:
            A new Task with due_date set to the next occurrence, or None if the
            task frequency is as_needed.
        """
        if self.frequency == "daily":
            next_date = from_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = from_date + timedelta(weeks=1)
        else:
            return None   # as_needed tasks are not rescheduled automatically

        return Task(
            name=self.name,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            frequency=self.frequency,
            time_of_day=self.time_of_day,
            due_date=next_date,
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a care task to this pet's task list.

        Duplicate detection is based on name + due_date so that a rescheduled
        instance (different due_date) can coexist with its completed predecessor.
        """
        if any(t.name == task.name and t.due_date == task.due_date for t in self.tasks):
            raise ValueError(f"Task '{task.name}' for {task.due_date or 'no date'} already exists for {self.name}.")
        self.tasks.append(task)

    def complete_task(self, task_name: str, today: date):
        """Mark a task as complete and automatically queue the next occurrence.

        Finds the first incomplete task matching task_name, marks it done, then
        calls reschedule() to append the next instance to this pet's task list.
        The completed record is kept in the list for history.

        Frequency behaviour:
          - daily    → next instance due tomorrow
          - weekly   → next instance due in 7 days
          - as_needed → marked complete only; no new instance is created

        Args:
            task_name: The name of the task to complete.
            today:     The date of completion; used to compute the next due date.

        Raises:
            ValueError: If no incomplete task with the given name exists for this pet.
        """
        task = next(
            (t for t in self.tasks if t.name == task_name and not t.is_completed),
            None
        )
        if task is None:
            raise ValueError(f"No incomplete task named '{task_name}' found for {self.name}.")

        task.mark_complete()

        next_task = task.reschedule(today)
        if next_task is not None:
            self.tasks.append(next_task)

    def remove_task(self, task_name: str):
        """Remove a task from this pet's list by name."""
        self.tasks = [t for t in self.tasks if t.name != task_name]

    def get_tasks(self) -> list[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferred_time: str = "any"            # morning / afternoon / evening / any
    preferred_categories: list[str] = field(default_factory=list)
    avoid_categories: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's pet list."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"Pet '{pet.name}' already exists.")
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        return self.pets

    def set_available_time(self, minutes: int):
        """Update the owner's daily available time in minutes."""
        self.available_minutes = minutes

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of all tasks across all owned pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return tasks filtered by pet name and/or completion status.

        Args:
            pet_name:  If provided, only return tasks for that pet.
            completed: If True, return only completed tasks.
                       If False, return only incomplete tasks.
                       If None, return tasks regardless of completion status.
        """
        if pet_name is not None:
            pet = next((p for p in self.pets if p.name == pet_name), None)
            tasks = pet.get_tasks() if pet else []
        else:
            tasks = self.get_all_tasks()

        if completed is not None:
            tasks = [t for t in tasks if t.is_completed == completed]

        return tasks


def _task_window(task: Task) -> tuple[int, int] | None:
    """Parse a task's time_of_day into a numeric time window in minutes since midnight.

    Used as a shared helper by sort_by_time, detect_conflicts, and
    detect_cross_pet_conflicts to avoid duplicating HH:MM parsing logic.

    Args:
        task: The task whose time_of_day field will be parsed.

    Returns:
        A (start_min, end_min) tuple where start_min is minutes since midnight
        and end_min is start_min + task.duration. Returns None if time_of_day
        is an empty string (flexible task with no fixed time).
    """
    if not task.time_of_day:
        return None
    h, m = map(int, task.time_of_day.split(":"))
    start = h * 60 + m
    return (start, start + task.duration)


def detect_cross_pet_conflicts(schedulers: list["Scheduler"]) -> list[str]:
    """Check for time overlaps across different pets' scheduled tasks.

    Collects all timed tasks from every Scheduler, then compares every
    cross-pet pair using the overlap condition: a_start < b_end and b_start < a_end.
    Same-pet pairs are skipped since Scheduler.detect_conflicts() handles those.
    Flexible tasks (empty time_of_day) are excluded from comparison.

    This is a module-level function rather than a Scheduler method because it
    requires access to multiple Scheduler instances simultaneously.

    Args:
        schedulers: A list of Scheduler instances, one per pet, each with
                    scheduled_tasks already populated by generate_plan().

    Returns:
        A list of human-readable warning strings describing each overlap.
        Returns an empty list if no cross-pet conflicts are found.
    """
    warnings = []

    # Collect (start, end, task, pet_name) for every timed task across all schedulers
    timed: list[tuple[int, int, Task, str]] = []
    for sched in schedulers:
        for t in sched.scheduled_tasks:
            window = _task_window(t)
            if window:
                timed.append((*window, t, sched.pet.name))

    for i, (a_start, a_end, a, a_pet) in enumerate(timed):
        for b_start, b_end, b, b_pet in timed[i + 1:]:
            if a_pet == b_pet:
                continue  # same-pet conflicts handled by Scheduler.detect_conflicts()
            if a_start < b_end and b_start < a_end:
                warnings.append(
                    f"  WARNING: '{a.name}' for {a_pet} "
                    f"({a.time_of_day}, {a.duration} min) overlaps with "
                    f"'{b.name}' for {b_pet} "
                    f"({b.time_of_day}, {b.duration} min)."
                )

    return warnings


@dataclass
class Scheduler:
    owner: Owner
    pet: Pet
    date: date
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    reasoning: str = ""

    def urgency_score(self, task: Task) -> int:
        """Compute a numeric urgency score combining priority and frequency.

        Scoring breakdown:
          Priority base  — high: 100 | medium: 50 | low: 10
          Frequency boost — daily: +20 | weekly: +5 | as_needed: +0

        A higher score means the task is scheduled earlier in generate_plan.
        Example: a high-priority daily task scores 120; a medium weekly scores 55.

        Args:
            task: The task to score.

        Returns:
            An integer urgency score. Higher values indicate greater urgency.
        """
        base = {"high": 100, "medium": 50, "low": 10}.get(task.priority, 10)
        freq_boost = {"daily": 20, "weekly": 5, "as_needed": 0}.get(task.frequency, 0)
        return base + freq_boost

    def detect_conflicts(self) -> list[str]:
        """Check scheduled tasks for time window overlaps within this pet's schedule.

        Compares every pair of timed tasks using the overlap condition:
            a_start < b_end  and  b_start < a_end
        where start and end are minutes since midnight derived from time_of_day
        and duration. Flexible tasks (empty time_of_day) are excluded.

        Called automatically at the end of generate_plan(). Results are stored
        in self.conflicts so they can be read after the fact without re-running.
        Never raises an exception — all issues are surfaced as warning strings.

        Returns:
            A list of warning strings, one per overlapping pair. Also stored in
            self.conflicts. Returns an empty list if no conflicts are found.
        """
        warnings = []
        timed: list[tuple[Task, tuple[int, int]]] = []
        for t in self.scheduled_tasks:
            w = _task_window(t)
            if w is not None:
                timed.append((t, w))

        for i, (a, (a_start, a_end)) in enumerate(timed):
            for b, (b_start, b_end) in timed[i + 1:]:
                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"  WARNING: '{a.name}' ({a.time_of_day}, {a.duration} min) "
                        f"overlaps with '{b.name}' ({b.time_of_day}, {b.duration} min) "
                        f"for {self.pet.name}."
                    )

        self.conflicts = warnings
        return warnings

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort a list of tasks chronologically by their time_of_day attribute.

        Timed tasks are sorted by converting "HH:MM" to total minutes since
        midnight. Flexible tasks (empty string) are placed after all timed tasks.
        The input list is not mutated; a new sorted list is returned.

        Args:
            tasks: The list of Task objects to sort.

        Returns:
            A new list sorted earliest-to-latest, with flexible tasks at the end.
        """
        def time_key(t: Task):
            if not t.time_of_day:
                return (1, 0)   # flexible → last
            h, m = map(int, t.time_of_day.split(":"))
            return (0, h * 60 + m)
        return sorted(tasks, key=time_key)

    def filter_tasks(self) -> list[Task]:
        """Return schedulable tasks for self.date.

        Excludes:
        - avoided categories
        - completed tasks
        - as_needed tasks (require manual triggering)
        - weekly tasks not due this weekday
        - tasks with a due_date set to a different day (future rescheduled instances)
        """
        return [
            t for t in self.pet.get_tasks()
            if t.category not in self.owner.avoid_categories
            and not t.is_completed
            and t.frequency != "as_needed"
            and not (t.frequency == "weekly" and self.date.weekday() != 0)
            and (t.due_date is None or t.due_date == self.date)
        ]

    def generate_plan(self):
        """Build the owner's daily care schedule for self.pet on self.date.

        Algorithm (three phases):
          1. Filter  — calls filter_tasks() to remove ineligible tasks.
          2. Sort    — ranks candidates by a three-key tuple:
                         (-urgency_score, not_in_preferred_categories, duration)
                       Higher urgency goes first; within equal urgency, preferred
                       categories are promoted; shortest task breaks remaining ties.
          3. Pack    — iterates in sorted order and greedily schedules each task
                       if it fits within the remaining time budget (first-fit).
                       Tasks that do not fit are moved to skipped_tasks.

        After packing, sort_by_time reorders scheduled_tasks chronologically for
        display, detect_conflicts runs automatically, and explain_reasoning is
        called to populate self.reasoning.

        Tradeoff: greedy first-fit is fast but not optimal. A high-urgency task
        that narrowly exceeds the budget is dropped even if rearranging smaller
        tasks would have created room for it.
        """
        sorted_tasks = sorted(
            self.filter_tasks(),
            key=lambda t: (
                -self.urgency_score(t),                              # higher urgency first
                t.category not in self.owner.preferred_categories,   # preferred categories first
                t.duration                                            # shorter tasks as tie-breaker
            )
        )

        time_remaining = self.owner.available_minutes
        self.scheduled_tasks = []
        self.skipped_tasks = []

        for task in sorted_tasks:
            if task.duration <= time_remaining:
                self.scheduled_tasks.append(task)
                time_remaining -= task.duration
            else:
                self.skipped_tasks.append(task)

        # Order the final schedule chronologically by task time
        self.scheduled_tasks = self.sort_by_time(self.scheduled_tasks)
        self.detect_conflicts()
        self.reasoning = self.explain_reasoning()

    def explain_reasoning(self) -> str:
        """Build a human-readable explanation of scheduling decisions."""
        lines = [
            f"Scheduled {len(self.scheduled_tasks)} tasks for {self.pet.name} "
            f"within {self.owner.available_minutes} available minutes."
        ]
        if self.owner.preferred_categories:
            lines.append(f"Prioritized preferred categories: {', '.join(self.owner.preferred_categories)}.")
        if self.owner.avoid_categories:
            lines.append(f"Excluded avoided categories: {', '.join(self.owner.avoid_categories)}.")
        timed = [t for t in self.scheduled_tasks if t.time_of_day]
        if timed:
            lines.append("Tasks with set times are ordered chronologically.")
        if self.skipped_tasks:
            skipped_names = ", ".join(t.name for t in self.skipped_tasks)
            lines.append(f"Skipped due to time constraints: {skipped_names}.")
        return " ".join(lines)

    def get_summary(self) -> str:
        """Return a one-line summary of the scheduled plan."""
        total = sum(t.duration for t in self.scheduled_tasks)
        return f"{len(self.scheduled_tasks)} tasks scheduled for {self.pet.name} ({total} min total)"

    def display(self):
        """Print the full daily plan to the terminal."""
        print(f"\n--- Daily Plan for {self.pet.name} | {self.date} ---")
        print(f"Owner: {self.owner.name} | Available: {self.owner.available_minutes} min\n")
        print("Scheduled Tasks:")
        for t in self.scheduled_tasks:
            time_str = t.time_of_day if t.time_of_day else "any time"
            print(f"  [{t.priority.upper()}] {t.name} — {t.duration} min ({t.category}, {time_str})")
        if self.skipped_tasks:
            print("\nSkipped Tasks:")
            for t in self.skipped_tasks:
                print(f"  {t.name} — {t.duration} min (not enough time)")
        if self.conflicts:
            print("\nConflicts Detected:")
            for w in self.conflicts:
                print(w)
        print(f"\nReasoning: {self.reasoning}")
