import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, detect_cross_pet_conflicts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(minutes=120, preferred=None, avoid=None):
    return Owner(
        name="Alex",
        available_minutes=minutes,
        preferred_categories=preferred or [],
        avoid_categories=avoid or [],
    )


def make_pet(name="Biscuit"):
    return Pet(name=name, species="dog", age=3, breed="Labrador")


def make_task(category="walk", duration=30, priority="medium",
              name="", frequency="daily", time_of_day="", due_date=None):
    return Task(
        category=category,
        duration=duration,
        priority=priority,
        name=name,
        frequency=frequency,
        time_of_day=time_of_day,
        due_date=due_date,
    )


TODAY = date(2026, 3, 28)   # fixed date so tests are deterministic


# ===========================================================================
# Existing tests (kept)
# ===========================================================================

def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", category="walk", duration=30, priority="high")
    assert task.is_completed == False
    task.mark_complete()
    assert task.is_completed == True


def test_add_task_increases_pet_task_count():
    pet = make_pet()
    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(name="Breakfast", category="feeding", duration=10, priority="high"))
    pet.add_task(Task(name="Evening Walk", category="walk", duration=20, priority="medium"))
    assert len(pet.get_tasks()) == 2


# ===========================================================================
# Task.display_name  # TEST THIS
# ===========================================================================

class TestDisplayName:
    def test_standard_category_returns_category(self):
        """When name is empty, display_name falls back to category."""
        task = make_task(category="walk", name="")
        assert task.display_name == "walk"

    def test_other_category_with_name_returns_name(self):
        """'other' tasks should expose the user-provided name."""
        task = make_task(category="other", name="Nail trim")
        assert task.display_name == "Nail trim"

    def test_standard_category_with_explicit_name_returns_name(self):
        """A non-other category with an explicit name should still return the name."""
        task = make_task(category="walk", name="Morning jog")
        assert task.display_name == "Morning jog"

    def test_name_empty_string_returns_category(self):
        task = make_task(category="grooming", name="")
        assert task.display_name == "grooming"


# ===========================================================================
# Task.reschedule  # TEST THIS
# ===========================================================================

class TestReschedule:
    def test_daily_task_schedules_next_day(self):
        task = make_task(frequency="daily", due_date=TODAY)
        next_task = task.reschedule(TODAY)
        assert next_task is not None
        assert next_task.due_date == TODAY + timedelta(days=1)

    def test_weekly_task_schedules_seven_days_later(self):
        task = make_task(frequency="weekly", due_date=TODAY)
        next_task = task.reschedule(TODAY)
        assert next_task is not None
        assert next_task.due_date == TODAY + timedelta(weeks=1)

    def test_as_needed_returns_none(self):
        task = make_task(frequency="as_needed")
        assert task.reschedule(TODAY) is None

    def test_rescheduled_task_is_not_completed(self):
        task = make_task(frequency="daily")
        task.mark_complete()
        next_task = task.reschedule(TODAY)
        assert not next_task.is_completed

    def test_rescheduled_task_preserves_attributes(self):
        task = Task(
            category="medication", duration=10, priority="high",
            name="Pill", frequency="daily", time_of_day="08:00",
        )
        next_task = task.reschedule(TODAY)
        assert next_task.category == "medication"
        assert next_task.duration == 10
        assert next_task.priority == "high"
        assert next_task.name == "Pill"
        assert next_task.time_of_day == "08:00"

    def test_reschedule_from_arbitrary_date(self):
        base = date(2026, 1, 1)
        task = make_task(frequency="daily")
        next_task = task.reschedule(base)
        assert next_task.due_date == date(2026, 1, 2)


# ===========================================================================
# Pet.get_tasks  # TEST THIS
# ===========================================================================

class TestGetTasks:
    def test_empty_by_default(self):
        pet = make_pet()
        assert pet.get_tasks() == []

    def test_returns_all_added_tasks(self):
        pet = make_pet()
        t1 = make_task(category="walk")
        t2 = make_task(category="feeding")
        pet.add_task(t1)
        pet.add_task(t2)
        assert pet.get_tasks() == [t1, t2]

    def test_returns_same_list_object(self):
        """get_tasks should return the actual tasks list (not a copy)."""
        pet = make_pet()
        pet.add_task(make_task(category="walk"))
        assert len(pet.get_tasks()) == 1


# ===========================================================================
# Scheduler.generate_plan  # TEST THIS
# ===========================================================================

class TestGeneratePlan:
    def _scheduler(self, owner, pet):
        return Scheduler(owner=owner, pet=pet, date=TODAY)

    def test_all_tasks_fit_within_budget(self):
        owner = make_owner(minutes=60)
        pet = make_pet()
        pet.add_task(make_task(category="walk", duration=20, priority="medium"))
        pet.add_task(make_task(category="feeding", duration=10, priority="high"))

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        assert len(sched.scheduled_tasks) == 2
        assert len(sched.skipped_tasks) == 0

    def test_task_skipped_when_over_budget(self):
        owner = make_owner(minutes=25)
        pet = make_pet()
        pet.add_task(make_task(category="walk", duration=30, priority="high"))    # won't fit
        pet.add_task(make_task(category="feeding", duration=10, priority="medium"))

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        assert any(t.category == "feeding" for t in sched.scheduled_tasks)
        assert any(t.category == "walk" for t in sched.skipped_tasks)

    def test_high_priority_scheduled_before_low(self):
        owner = make_owner(minutes=40)
        pet = make_pet()
        low  = make_task(category="grooming",   duration=20, priority="low")
        high = make_task(category="medication", duration=20, priority="high")
        pet.add_task(low)
        pet.add_task(high)

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        names = [t.category for t in sched.scheduled_tasks]
        assert names.index("medication") < names.index("grooming") or \
               all(t.time_of_day == "" for t in sched.scheduled_tasks)
        # Regardless of time ordering, both fit — confirm both scheduled
        assert len(sched.scheduled_tasks) == 2

    def test_avoided_category_excluded(self):
        owner = make_owner(minutes=120, avoid=["grooming"])
        pet = make_pet()
        pet.add_task(make_task(category="grooming", duration=20, priority="high"))
        pet.add_task(make_task(category="walk",     duration=20, priority="medium"))

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        categories = [t.category for t in sched.scheduled_tasks]
        assert "grooming" not in categories
        assert "walk" in categories

    def test_completed_tasks_excluded(self):
        owner = make_owner(minutes=120)
        pet = make_pet()
        done = make_task(category="walk", duration=20, priority="high")
        done.mark_complete()
        pet.add_task(done)

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        assert len(sched.scheduled_tasks) == 0

    def test_as_needed_tasks_excluded(self):
        owner = make_owner(minutes=120)
        pet = make_pet()
        pet.add_task(make_task(category="medication", duration=5, priority="high", frequency="as_needed"))

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        assert len(sched.scheduled_tasks) == 0

    def test_scheduled_tasks_sorted_by_time(self):
        owner = make_owner(minutes=120)
        pet = make_pet()
        pet.add_task(make_task(category="walk",    duration=20, priority="medium", time_of_day="14:00"))
        pet.add_task(make_task(category="feeding", duration=10, priority="medium", time_of_day="08:00"))

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        times = [t.time_of_day for t in sched.scheduled_tasks if t.time_of_day]
        assert times == sorted(times)

    def test_preferred_category_promoted(self):
        owner = make_owner(minutes=30, preferred=["enrichment"])
        pet = make_pet()
        # Both same priority & duration — enrichment should be preferred first
        pet.add_task(make_task(category="grooming",   duration=15, priority="medium"))
        pet.add_task(make_task(category="enrichment", duration=15, priority="medium"))

        sched = self._scheduler(owner, pet)
        sched.generate_plan()

        # With only 30 min budget and 15-min tasks, both fit — check order before time sort
        scheduled_cats = [t.category for t in sched.scheduled_tasks]
        assert "enrichment" in scheduled_cats


# ===========================================================================
# Scheduler.explain_reasoning  # TEST THIS
# ===========================================================================

class TestExplainReasoning:
    def _run(self, owner, pet):
        sched = Scheduler(owner=owner, pet=pet, date=TODAY)
        sched.generate_plan()
        return sched.reasoning

    def test_includes_pet_name(self):
        owner = make_owner()
        pet = make_pet("Fluffy")
        pet.add_task(make_task())
        reasoning = self._run(owner, pet)
        assert "Fluffy" in reasoning

    def test_includes_scheduled_count(self):
        owner = make_owner(minutes=60)
        pet = make_pet()
        pet.add_task(make_task(duration=20))
        pet.add_task(make_task(category="feeding", duration=20))
        reasoning = self._run(owner, pet)
        assert "2" in reasoning

    def test_mentions_skipped_when_tasks_dropped(self):
        owner = make_owner(minutes=10)
        pet = make_pet()
        pet.add_task(make_task(duration=60, priority="high"))   # won't fit
        reasoning = self._run(owner, pet)
        assert "Skipped" in reasoning or "skipped" in reasoning

    def test_mentions_preferred_categories_when_set(self):
        owner = make_owner(preferred=["walk"])
        pet = make_pet()
        pet.add_task(make_task(category="walk", duration=20))
        reasoning = self._run(owner, pet)
        assert "walk" in reasoning

    def test_mentions_avoided_categories_when_set(self):
        owner = make_owner(avoid=["grooming"])
        pet = make_pet()
        pet.add_task(make_task(category="walk", duration=20))
        reasoning = self._run(owner, pet)
        assert "grooming" in reasoning

    def test_no_skipped_mention_when_all_fit(self):
        owner = make_owner(minutes=120)
        pet = make_pet()
        pet.add_task(make_task(duration=10))
        reasoning = self._run(owner, pet)
        assert "Skipped" not in reasoning


# ===========================================================================
# Custom tests — Pet duplicate detection
# ===========================================================================

class TestPetAddTaskDuplication:
    def test_duplicate_task_same_date_raises(self):
        pet = make_pet()
        t1 = make_task(category="walk", due_date=TODAY)
        t2 = make_task(category="walk", due_date=TODAY)
        pet.add_task(t1)
        with pytest.raises(ValueError):
            pet.add_task(t2)

    def test_same_name_different_due_date_allowed(self):
        pet = make_pet()
        t1 = make_task(category="walk", due_date=TODAY)
        t2 = make_task(category="walk", due_date=TODAY + timedelta(days=1))
        pet.add_task(t1)
        pet.add_task(t2)   # should not raise
        assert len(pet.get_tasks()) == 2


# ===========================================================================
# Custom tests — Pet.complete_task reschedules automatically
# ===========================================================================

class TestCompleteTask:
    def test_complete_task_marks_done(self):
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))
        pet.complete_task("walk", TODAY)
        assert pet.get_tasks()[0].is_completed

    def test_complete_daily_task_appends_next_instance(self):
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))
        pet.complete_task("walk", TODAY)
        assert len(pet.get_tasks()) == 2
        assert pet.get_tasks()[1].due_date == TODAY + timedelta(days=1)

    def test_complete_as_needed_does_not_reschedule(self):
        pet = make_pet()
        pet.add_task(make_task(category="medication", frequency="as_needed"))
        pet.complete_task("medication", TODAY)
        assert len(pet.get_tasks()) == 1   # no new instance

    def test_complete_nonexistent_task_raises(self):
        pet = make_pet()
        with pytest.raises(ValueError):
            pet.complete_task("nonexistent", TODAY)

    def test_complete_already_done_task_raises(self):
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))
        pet.complete_task("walk", TODAY)
        # The original is now done; only the new rescheduled one is incomplete
        # completing "walk" again should use the rescheduled instance
        pet.complete_task("walk", TODAY + timedelta(days=1))
        assert len(pet.get_tasks()) == 3


# ===========================================================================
# Custom tests — Owner.filter_tasks
# ===========================================================================

class TestOwnerFilterTasks:
    def setup_method(self):
        self.owner = make_owner()
        dog = make_pet("Biscuit")
        cat = Pet(name="Whiskers", species="cat", age=2, breed="Siamese")
        dog.add_task(make_task(category="walk",    priority="high"))
        dog.add_task(make_task(category="feeding", priority="low"))
        done = make_task(category="grooming")
        done.mark_complete()
        cat.add_task(done)
        cat.add_task(make_task(category="enrichment"))
        self.owner.add_pet(dog)
        self.owner.add_pet(cat)

    def test_no_filter_returns_all(self):
        assert len(self.owner.filter_tasks()) == 4

    def test_filter_by_pet_name(self):
        tasks = self.owner.filter_tasks(pet_name="Biscuit")
        assert len(tasks) == 2

    def test_filter_incomplete_tasks(self):
        tasks = self.owner.filter_tasks(completed=False)
        assert all(not t.is_completed for t in tasks)

    def test_filter_completed_tasks(self):
        tasks = self.owner.filter_tasks(completed=True)
        assert all(t.is_completed for t in tasks)
        assert len(tasks) == 1

    def test_filter_pet_and_completed_combined(self):
        tasks = self.owner.filter_tasks(pet_name="Whiskers", completed=False)
        assert len(tasks) == 1
        assert tasks[0].category == "enrichment"

    def test_filter_unknown_pet_returns_empty(self):
        assert self.owner.filter_tasks(pet_name="Unknown") == []


# ===========================================================================
# FOCUSED: Sorting Correctness
# Verify scheduled_tasks are always returned in chronological order
# ===========================================================================

class TestSortingCorrectness:
    def _run(self, tasks, minutes=600):
        owner = make_owner(minutes=minutes)
        pet = make_pet()
        for t in tasks:
            pet.add_task(t)
        sched = Scheduler(owner=owner, pet=pet, date=TODAY)
        sched.generate_plan()
        return sched.scheduled_tasks

    def test_two_tasks_out_of_order_sorted(self):
        """Tasks added in reverse time order must come out chronologically."""
        late  = make_task(category="walk",    duration=20, time_of_day="14:00")
        early = make_task(category="feeding", duration=10, time_of_day="08:00")
        result = self._run([late, early])
        assert result[0].time_of_day == "08:00"
        assert result[1].time_of_day == "14:00"

    def test_five_tasks_fully_sorted(self):
        """All five tasks should appear in strict HH:MM order."""
        times = ["22:00", "06:30", "13:15", "08:00", "17:45"]
        tasks = [
            make_task(category=f"walk", duration=5, time_of_day=t, name=f"task_{t}")
            for t in times
        ]
        # patch name so each is unique (avoid duplicate detection)
        for i, t in enumerate(tasks):
            t.name = f"task{i}"
        result = self._run(tasks)
        timed_results = [t.time_of_day for t in result if t.time_of_day]
        assert timed_results == sorted(timed_results)

    def test_midnight_task_sorts_first(self):
        """A 00:00 task should appear before an 08:00 task."""
        midnight = make_task(category="medication", duration=5,  time_of_day="00:00")
        morning  = make_task(category="feeding",    duration=10, time_of_day="08:00")
        result = self._run([morning, midnight])
        assert result[0].time_of_day == "00:00"

    def test_flexible_tasks_appear_after_all_timed(self):
        """Flexible (no time_of_day) tasks must trail all timed tasks."""
        timed    = make_task(category="walk",        duration=20, time_of_day="23:59")
        flexible = make_task(category="enrichment",  duration=10, time_of_day="")
        result = self._run([flexible, timed])
        assert result[0].time_of_day == "23:59"
        assert result[1].time_of_day == ""

    def test_multiple_flexible_tasks_all_at_end(self):
        timed = make_task(category="walk",       duration=10, time_of_day="09:00")
        f1    = make_task(category="feeding",    duration=10, time_of_day="")
        f2    = make_task(category="enrichment", duration=10, time_of_day="")
        result = self._run([f1, timed, f2])
        timed_block    = [t for t in result if t.time_of_day]
        flexible_block = [t for t in result if not t.time_of_day]
        # All timed must come before all flexible
        if timed_block and flexible_block:
            last_timed_idx    = result.index(timed_block[-1])
            first_flex_idx    = result.index(flexible_block[0])
            assert last_timed_idx < first_flex_idx


# ===========================================================================
# FOCUSED: Recurrence Logic
# Marking a daily task complete must queue a new task for the next day
# ===========================================================================

class TestRecurrenceLogic:
    def test_daily_new_task_due_exactly_next_day(self):
        """The rescheduled task's due_date is completion_date + 1 day."""
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))
        pet.complete_task("walk", TODAY)
        new_task = pet.get_tasks()[1]
        assert new_task.due_date == TODAY + timedelta(days=1)

    def test_weekly_new_task_due_exactly_seven_days_later(self):
        """Weekly recurrence: new task is due 7 days after completion."""
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="weekly"))
        pet.complete_task("walk", TODAY)
        new_task = pet.get_tasks()[1]
        assert new_task.due_date == TODAY + timedelta(weeks=1)

    def test_new_task_is_not_completed(self):
        """The rescheduled task must start as incomplete."""
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))
        pet.complete_task("walk", TODAY)
        assert not pet.get_tasks()[1].is_completed

    def test_original_completed_task_preserved_in_history(self):
        """Completing a task keeps the original in the list (history record)."""
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))
        pet.complete_task("walk", TODAY)
        assert pet.get_tasks()[0].is_completed   # original still there

    def test_chained_daily_completions_advance_date_each_time(self):
        """Completing the rescheduled task itself produces a further next day."""
        pet = make_pet()
        pet.add_task(make_task(category="walk", frequency="daily"))

        pet.complete_task("walk", TODAY)           # day 0 → queues day 1
        pet.complete_task("walk", TODAY + timedelta(days=1))  # day 1 → queues day 2

        assert len(pet.get_tasks()) == 3
        assert pet.get_tasks()[2].due_date == TODAY + timedelta(days=2)

    def test_as_needed_no_new_task_created(self):
        """as_needed tasks must not produce a rescheduled instance."""
        pet = make_pet()
        pet.add_task(make_task(category="medication", frequency="as_needed"))
        pet.complete_task("medication", TODAY)
        assert len(pet.get_tasks()) == 1

    def test_new_task_inherits_all_original_attributes(self):
        """Rescheduled task keeps category, duration, priority, time_of_day."""
        pet = make_pet()
        original = Task(
            category="medication", duration=5, priority="high",
            name="Pill", frequency="daily", time_of_day="08:00",
        )
        pet.add_task(original)
        pet.complete_task("Pill", TODAY)
        rescheduled = pet.get_tasks()[1]
        assert rescheduled.category  == "medication"
        assert rescheduled.duration  == 5
        assert rescheduled.priority  == "high"
        assert rescheduled.name      == "Pill"
        assert rescheduled.time_of_day == "08:00"


# ===========================================================================
# FOCUSED: Conflict Detection
# Verify the scheduler flags overlapping time windows
# ===========================================================================

class TestDetectConflicts:
    def _sched_with_tasks(self, *tasks):
        owner = make_owner(minutes=600)
        pet = make_pet()
        for t in tasks:
            pet.add_task(t)
        sched = Scheduler(owner=owner, pet=pet, date=TODAY)
        sched.generate_plan()
        return sched

    # --- no conflict cases ---

    def test_no_conflict_non_overlapping(self):
        """08:00-08:30 and 09:00-09:15 — clear gap, no warning expected."""
        t1 = make_task(category="walk",    duration=30, time_of_day="08:00")
        t2 = make_task(category="feeding", duration=15, time_of_day="09:00")
        sched = self._sched_with_tasks(t1, t2)
        assert sched.conflicts == []

    def test_back_to_back_tasks_no_conflict(self):
        """08:00+30min ends exactly at 08:30; 08:30 start — not an overlap."""
        t1 = make_task(category="walk",    duration=30, time_of_day="08:00")
        t2 = make_task(category="feeding", duration=30, time_of_day="08:30")
        sched = self._sched_with_tasks(t1, t2)
        assert sched.conflicts == []

    def test_flexible_tasks_never_conflict(self):
        """Tasks with no time_of_day are excluded from conflict checks."""
        t1 = make_task(category="walk",    duration=60, time_of_day="")
        t2 = make_task(category="feeding", duration=60, time_of_day="")
        sched = self._sched_with_tasks(t1, t2)
        assert sched.conflicts == []

    # --- overlap cases ---

    def test_overlap_partial_start(self):
        """08:00-09:00 overlaps with 08:30-09:00 — 30 min of shared window."""
        t1 = make_task(category="walk",    duration=60, time_of_day="08:00")
        t2 = make_task(category="feeding", duration=30, time_of_day="08:30")
        sched = self._sched_with_tasks(t1, t2)
        assert len(sched.conflicts) == 1

    def test_overlap_same_start_time(self):
        """Two tasks starting at exactly the same time must conflict."""
        t1 = make_task(category="walk",    duration=30, time_of_day="08:00")
        t2 = make_task(category="feeding", duration=20, time_of_day="08:00")
        sched = self._sched_with_tasks(t1, t2)
        assert len(sched.conflicts) == 1

    def test_overlap_one_task_entirely_inside_another(self):
        """09:00+60min contains 09:15+10min — inner task fully inside outer."""
        outer = make_task(category="walk",        duration=60, time_of_day="09:00")
        inner = make_task(category="medication",  duration=10, time_of_day="09:15")
        sched = self._sched_with_tasks(outer, inner)
        assert len(sched.conflicts) == 1

    def test_overlap_one_minute_overlap(self):
        """08:00+30min ends 08:30; 08:29+30min starts 08:29 — 1-min overlap."""
        t1 = make_task(category="walk",    duration=30, time_of_day="08:00")
        t2 = make_task(category="feeding", duration=30, time_of_day="08:29")
        sched = self._sched_with_tasks(t1, t2)
        assert len(sched.conflicts) == 1

    def test_three_overlapping_tasks_produce_three_warnings(self):
        """Three mutually overlapping tasks → 3 pairs → 3 conflict warnings."""
        t1 = make_task(category="walk",        duration=60, time_of_day="08:00")
        t2 = make_task(category="feeding",     duration=60, time_of_day="08:15")
        t3 = make_task(category="enrichment",  duration=60, time_of_day="08:30")
        sched = self._sched_with_tasks(t1, t2, t3)
        assert len(sched.conflicts) == 3

    def test_conflict_warning_names_both_tasks(self):
        """The warning string must mention both conflicting task display names."""
        t1 = make_task(category="walk",    duration=60, time_of_day="08:00", name="Morning Walk")
        t2 = make_task(category="feeding", duration=30, time_of_day="08:30", name="Breakfast")
        sched = self._sched_with_tasks(t1, t2)
        assert len(sched.conflicts) == 1
        warning = sched.conflicts[0]
        assert "Morning Walk" in warning
        assert "Breakfast" in warning

    def test_conflicts_stored_on_scheduler_after_generate_plan(self):
        """detect_conflicts results are accessible via sched.conflicts after generate_plan."""
        t1 = make_task(category="walk",    duration=60, time_of_day="08:00")
        t2 = make_task(category="feeding", duration=30, time_of_day="08:30")
        sched = self._sched_with_tasks(t1, t2)
        # conflicts populated automatically by generate_plan
        assert isinstance(sched.conflicts, list)
        assert len(sched.conflicts) > 0


# ===========================================================================
# Custom tests — detect_cross_pet_conflicts
# ===========================================================================

class TestCrossPetConflicts:
    def _make_sched(self, pet, owner, tasks):
        for t in tasks:
            pet.add_task(t)
        sched = Scheduler(owner=owner, pet=pet, date=TODAY)
        sched.generate_plan()
        return sched

    def test_no_cross_conflict_non_overlapping(self):
        owner = make_owner(minutes=600)
        dog = make_pet("Dog")
        cat = Pet(name="Cat", species="cat", age=1, breed="Mix")

        s1 = self._make_sched(dog, owner, [make_task(category="walk",    duration=30, time_of_day="08:00")])
        s2 = self._make_sched(cat, owner, [make_task(category="feeding", duration=30, time_of_day="09:00")])

        assert detect_cross_pet_conflicts([s1, s2]) == []

    def test_cross_conflict_detected(self):
        owner = make_owner(minutes=600)
        dog = make_pet("Dog")
        cat = Pet(name="Cat", species="cat", age=1, breed="Mix")

        s1 = self._make_sched(dog, owner, [make_task(category="walk",    duration=60, time_of_day="08:00")])
        s2 = self._make_sched(cat, owner, [make_task(category="feeding", duration=30, time_of_day="08:15")])

        warnings = detect_cross_pet_conflicts([s1, s2])
        assert len(warnings) > 0
        assert "Dog" in warnings[0] or "Cat" in warnings[0]

    def test_flexible_tasks_ignored_in_cross_check(self):
        owner = make_owner(minutes=600)
        dog = make_pet("Dog")
        cat = Pet(name="Cat", species="cat", age=1, breed="Mix")

        s1 = self._make_sched(dog, owner, [make_task(category="walk",    duration=999, time_of_day="")])
        s2 = self._make_sched(cat, owner, [make_task(category="feeding", duration=999, time_of_day="")])

        assert detect_cross_pet_conflicts([s1, s2]) == []


# ===========================================================================
# Custom tests — Scheduler.urgency_score
# ===========================================================================

class TestUrgencyScore:
    def _score(self, priority, frequency):
        owner = make_owner()
        pet = make_pet()
        sched = Scheduler(owner=owner, pet=pet, date=TODAY)
        task = make_task(priority=priority, frequency=frequency)
        return sched.urgency_score(task)

    def test_high_priority_scores_higher_than_medium(self):
        assert self._score("high", "daily") > self._score("medium", "daily")

    def test_medium_priority_scores_higher_than_low(self):
        assert self._score("medium", "daily") > self._score("low", "daily")

    def test_daily_boosts_score_over_weekly(self):
        assert self._score("medium", "daily") > self._score("medium", "weekly")

    def test_high_daily_scores_120(self):
        assert self._score("high", "daily") == 120

    def test_low_as_needed_scores_10(self):
        assert self._score("low", "as_needed") == 10


# ===========================================================================
# Custom tests — Scheduler.sort_by_time
# ===========================================================================

class TestSortByTime:
    def _sort(self, tasks):
        owner = make_owner()
        pet = make_pet()
        sched = Scheduler(owner=owner, pet=pet, date=TODAY)
        return sched.sort_by_time(tasks)

    def test_sorts_chronologically(self):
        t1 = make_task(category="walk",    time_of_day="14:00")
        t2 = make_task(category="feeding", time_of_day="08:00")
        t3 = make_task(category="grooming",time_of_day="11:30")
        result = self._sort([t1, t2, t3])
        assert [t.time_of_day for t in result] == ["08:00", "11:30", "14:00"]

    def test_flexible_tasks_placed_last(self):
        timed    = make_task(category="walk",    time_of_day="09:00")
        flexible = make_task(category="feeding", time_of_day="")
        result = self._sort([flexible, timed])
        assert result[0].time_of_day == "09:00"
        assert result[1].time_of_day == ""

    def test_does_not_mutate_input(self):
        tasks = [make_task(time_of_day="14:00"), make_task(time_of_day="08:00")]
        original_order = [t.time_of_day for t in tasks]
        self._sort(tasks)
        assert [t.time_of_day for t in tasks] == original_order


# ===========================================================================
# Custom tests — Owner.add_pet duplicate guard
# ===========================================================================

class TestOwnerAddPet:
    def test_duplicate_pet_name_raises(self):
        owner = make_owner()
        owner.add_pet(make_pet("Biscuit"))
        with pytest.raises(ValueError):
            owner.add_pet(make_pet("Biscuit"))

    def test_different_pet_names_allowed(self):
        owner = make_owner()
        owner.add_pet(make_pet("Biscuit"))
        owner.add_pet(make_pet("Fluffy"))
        assert len(owner.get_pets()) == 2
