import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", category="walk", duration=30, priority="high")
    assert task.is_completed == False
    task.mark_complete()
    assert task.is_completed == True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", species="dog", age=3, breed="Labrador")
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(name="Breakfast", category="feeding", duration=10, priority="high"))
    pet.add_task(Task(name="Evening Walk", category="walk", duration=20, priority="medium"))
    assert len(pet.get_tasks()) == 2
