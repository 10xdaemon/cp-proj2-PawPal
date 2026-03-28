from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    name: str
    category: str        # walk / feeding / medication / grooming / enrichment
    duration: int        # minutes
    priority: str        # high / medium / low
    frequency: str = "daily"   # daily / weekly / as_needed
    time_of_day: str = "any"   # morning / afternoon / evening / any
    is_completed: bool = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.is_completed = True

    def mark_incomplete(self):
        """Reset this task to incomplete."""
        self.is_completed = False

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"


@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

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


@dataclass
class Scheduler:
    owner: Owner
    pet: Pet
    date: date
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""

    def generate_plan(self):
        """Build the daily plan by sorting, filtering, and fitting tasks within available time."""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_tasks = sorted(
            self.filter_tasks(),
            key=lambda t: (priority_order.get(t.priority, 3), t.category not in self.owner.preferred_categories)
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

        self.reasoning = self.explain_reasoning()

    def filter_tasks(self) -> list[Task]:
        """Return tasks that are not in the owner's avoided categories."""
        return [
            t for t in self.pet.get_tasks()
            if t.category not in self.owner.avoid_categories
        ]

    def explain_reasoning(self) -> str:
        """Build a human-readable explanation of scheduling decisions."""
        lines = [
            f"Scheduled {len(self.scheduled_tasks)} tasks for {self.pet.name} within {self.owner.available_minutes} available minutes."
        ]
        if self.owner.preferred_categories:
            lines.append(f"Prioritized preferred categories: {', '.join(self.owner.preferred_categories)}.")
        if self.owner.avoid_categories:
            lines.append(f"Excluded avoided categories: {', '.join(self.owner.avoid_categories)}.")
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
            print(f"  [{t.priority.upper()}] {t.name} — {t.duration} min ({t.category}, {t.time_of_day})")
        if self.skipped_tasks:
            print("\nSkipped Tasks:")
            for t in self.skipped_tasks:
                print(f"  {t.name} — {t.duration} min (not enough time)")
        print(f"\nReasoning: {self.reasoning}")
