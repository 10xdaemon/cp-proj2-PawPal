from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    name: str
    category: str        # walk / feeding / medication / grooming / enrichment
    duration: int        # minutes
    priority: str        # high / medium / low
    is_completed: bool = False

    def mark_complete(self):
        pass

    def mark_incomplete(self):
        pass

    def is_high_priority(self) -> bool:
        return False


@dataclass
class Pet:
    name: str
    species: str
    age: int
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        pass

    def remove_task(self, task_name: str):
        pass

    def get_tasks(self) -> list[Task]:
        return []


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        pass

    def get_pets(self) -> list[Pet]:
        return []

    def set_available_time(self, minutes: int):
        pass


@dataclass
class Scheduler:
    owner: Owner
    pet: Pet
    date: date
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""

    def generate_plan(self):
        pass

    def filter_tasks(self) -> list[Task]:
        return []

    def explain_reasoning(self) -> str:
        return ""

    def get_summary(self) -> str:
        return ""

    def display(self):
        pass
