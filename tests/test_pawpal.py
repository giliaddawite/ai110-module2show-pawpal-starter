"""
tests/test_pawpal.py
--------------------
Unit tests for PawPal+ core logic.

Test plan (5 core behaviors + edge cases):
  1. generate_plan  — priority order, budget limit, empty pet, zero budget
  2. sort_by_time   — chronological sort, untimed tasks go last, empty list
  3. filter_tasks   — by status, by category, AND logic, no matches
  4. detect_conflicts — overlap, touching edges, same start, no start_time
  5. Recurring tasks  — daily/weekly next-occurrence, one-time None, auto-append
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, PRIORITY_MAP


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def owner():
    return Owner("Jordan", available_minutes=60)

@pytest.fixture
def pet():
    return Pet("Mochi", species="dog", breed="Shiba Inu", age=3)

@pytest.fixture
def scheduler(owner, pet):
    """Scheduler pre-loaded with three tasks at different priorities."""
    pet.add_task(Task("Walk",    "walk",       duration_minutes=30, priority=PRIORITY_MAP["high"]))
    pet.add_task(Task("Feed",    "feed",       duration_minutes=10, priority=PRIORITY_MAP["high"]))
    pet.add_task(Task("Groom",   "grooming",   duration_minutes=25, priority=PRIORITY_MAP["low"]))
    owner.add_pet(pet)
    return Scheduler(owner, pet)


# ===========================================================================
# 1. generate_plan
# ===========================================================================

class TestGeneratePlan:

    def test_high_priority_scheduled_before_low(self, scheduler):
        """High-priority tasks appear before low-priority ones in the plan."""
        plan = scheduler.generate_plan()
        priorities = [t.priority for t in plan]
        assert priorities == sorted(priorities), "Plan is not sorted by priority"

    def test_plan_does_not_exceed_budget(self, scheduler):
        """Total plan duration never exceeds the owner's available minutes."""
        plan = scheduler.generate_plan()
        assert sum(t.duration_minutes for t in plan) <= scheduler.owner.available_minutes

    def test_low_priority_task_skipped_when_over_budget(self, scheduler):
        """Groom (25 min, low) should be skipped — Walk+Feed already use 40 of 60 min,
        leaving only 20 min which is less than Groom's 25 min."""
        plan = scheduler.generate_plan()
        names = [t.name for t in plan]
        assert "Groom" not in names

    def test_empty_pet_returns_empty_plan(self, owner):
        """A pet with no tasks produces an empty plan — no crash."""
        empty_pet = Pet("Ghost", "cat", "Persian", 1)
        owner.add_pet(empty_pet)
        s = Scheduler(owner, empty_pet)
        assert s.generate_plan() == []

    def test_zero_budget_returns_empty_plan(self, pet):
        """An owner with 0 available minutes cannot schedule any task."""
        broke_owner = Owner("Broke", available_minutes=0)
        broke_owner.add_pet(pet)
        pet.add_task(Task("Walk", "walk", duration_minutes=1, priority=1))
        s = Scheduler(broke_owner, pet)
        assert s.generate_plan() == []

    def test_task_exactly_filling_budget_is_included(self, owner, pet):
        """A single task whose duration equals the budget should be scheduled."""
        exact = Task("Exact", "walk", duration_minutes=60, priority=1)
        pet.add_task(exact)
        owner.add_pet(pet)
        s = Scheduler(owner, pet)
        assert exact in s.generate_plan()

    def test_completed_tasks_not_in_plan(self, owner, pet):
        """Already-completed tasks must never appear in a new plan."""
        done = Task("Done walk", "walk", duration_minutes=10, priority=1)
        done.complete()
        pet.add_task(done)
        owner.add_pet(pet)
        s = Scheduler(owner, pet)
        assert done not in s.generate_plan()

    def test_start_times_assigned_after_generate(self, scheduler):
        """Every task in the plan should have a non-empty start_time after generate_plan()."""
        plan = scheduler.generate_plan(start_hour=8)
        for task in plan:
            assert task.start_time != "", f"{task.name} has no start_time"

    def test_start_times_are_sequential(self, scheduler):
        """Start times must be in strictly increasing order."""
        plan = scheduler.generate_plan(start_hour=8)
        times = [task.start_time for task in plan]
        assert times == sorted(times)


# ===========================================================================
# 2. sort_by_time
# ===========================================================================

class TestSortByTime:

    def test_tasks_sorted_chronologically(self, owner, pet):
        """Tasks with earlier HH:MM start_time come first."""
        owner.add_pet(pet)
        t1 = Task("Late",  "walk", duration_minutes=10, priority=1, start_time="10:00")
        t2 = Task("Early", "feed", duration_minutes=10, priority=1, start_time="08:00")
        t3 = Task("Mid",   "meds", duration_minutes=10, priority=1, start_time="09:30")
        for t in [t1, t2, t3]:
            pet.add_task(t)
        s = Scheduler(owner, pet)
        sorted_tasks = s.sort_by_time([t1, t2, t3])
        assert [t.name for t in sorted_tasks] == ["Early", "Mid", "Late"]

    def test_tasks_without_start_time_go_last(self, owner, pet):
        """Tasks with no start_time should sort after all timed tasks."""
        owner.add_pet(pet)
        timed    = Task("Timed",   "walk", duration_minutes=10, priority=1, start_time="09:00")
        untimed  = Task("Untimed", "feed", duration_minutes=10, priority=1, start_time="")
        pet.add_task(timed)
        pet.add_task(untimed)
        s = Scheduler(owner, pet)
        result = s.sort_by_time([untimed, timed])
        assert result[0].name == "Timed"
        assert result[-1].name == "Untimed"

    def test_sort_empty_list(self, owner, pet):
        """sort_by_time on an empty list returns an empty list without error."""
        owner.add_pet(pet)
        s = Scheduler(owner, pet)
        assert s.sort_by_time([]) == []

    def test_single_task_list_unchanged(self, owner, pet):
        """sort_by_time on a single-item list returns that same item."""
        t = Task("Solo", "walk", duration_minutes=10, priority=1, start_time="08:00")
        pet.add_task(t)
        owner.add_pet(pet)
        s = Scheduler(owner, pet)
        assert s.sort_by_time([t]) == [t]


# ===========================================================================
# 3. filter_tasks
# ===========================================================================

class TestFilterTasks:

    @pytest.fixture
    def mixed_tasks(self, owner, pet):
        """Pet with a mix of completed/pending and different categories."""
        t_done  = Task("Done walk",  "walk",      duration_minutes=30, priority=1)
        t_pend  = Task("Pending med","meds",      duration_minutes=5,  priority=1)
        t_feed  = Task("Breakfast",  "feed",      duration_minutes=10, priority=2)
        t_done.complete()
        for t in [t_done, t_pend, t_feed]:
            pet.add_task(t)
        owner.add_pet(pet)
        return Scheduler(owner, pet), [t_done, t_pend, t_feed]

    def test_filter_pending_only(self, mixed_tasks):
        s, tasks = mixed_tasks
        result = s.filter_tasks(tasks, completed=False)
        assert all(not t.is_completed for t in result)
        assert len(result) == 2

    def test_filter_completed_only(self, mixed_tasks):
        s, tasks = mixed_tasks
        result = s.filter_tasks(tasks, completed=True)
        assert all(t.is_completed for t in result)
        assert len(result) == 1

    def test_filter_by_category(self, mixed_tasks):
        s, tasks = mixed_tasks
        result = s.filter_tasks(tasks, category="meds")
        assert all(t.category == "meds" for t in result)
        assert len(result) == 1

    def test_filter_combined_and_logic(self, mixed_tasks):
        """completed=False AND category='meds' should return only pending meds."""
        s, tasks = mixed_tasks
        result = s.filter_tasks(tasks, completed=False, category="meds")
        assert len(result) == 1
        assert result[0].name == "Pending med"

    def test_filter_no_match_returns_empty(self, mixed_tasks):
        """Filtering for a category with no tasks returns an empty list."""
        s, tasks = mixed_tasks
        result = s.filter_tasks(tasks, category="enrichment")
        assert result == []

    def test_filter_no_args_returns_all(self, mixed_tasks):
        """Calling filter_tasks with no filter args returns the original list unchanged."""
        s, tasks = mixed_tasks
        result = s.filter_tasks(tasks)
        assert result == tasks


# ===========================================================================
# 4. detect_conflicts
# ===========================================================================

class TestDetectConflicts:

    @pytest.fixture
    def sched(self, owner, pet):
        owner.add_pet(pet)
        return Scheduler(owner, pet)

    def test_overlapping_tasks_flagged(self, sched):
        """Two tasks whose windows overlap should be returned as a conflict pair."""
        t1 = Task("A", "walk", duration_minutes=45, priority=1, start_time="09:00")
        t2 = Task("B", "meds", duration_minutes=30, priority=1, start_time="09:20")
        conflicts = sched.detect_conflicts([t1, t2])
        assert len(conflicts) == 1
        assert (t1, t2) in conflicts

    def test_touching_tasks_not_a_conflict(self, sched):
        """Task A ending exactly when Task B starts is NOT an overlap (strict inequality)."""
        t1 = Task("A", "walk", duration_minutes=30, priority=1, start_time="09:00")  # ends 09:30
        t2 = Task("B", "feed", duration_minutes=10, priority=1, start_time="09:30")  # starts 09:30
        conflicts = sched.detect_conflicts([t1, t2])
        assert conflicts == []

    def test_same_start_time_is_conflict(self, sched):
        """Two tasks starting at the exact same time always conflict."""
        t1 = Task("A", "walk", duration_minutes=20, priority=1, start_time="08:00")
        t2 = Task("B", "feed", duration_minutes=10, priority=1, start_time="08:00")
        conflicts = sched.detect_conflicts([t1, t2])
        assert len(conflicts) == 1

    def test_single_task_no_conflict(self, sched):
        """A single task has no pair to compare — result must be empty."""
        t = Task("Solo", "walk", duration_minutes=30, priority=1, start_time="09:00")
        assert sched.detect_conflicts([t]) == []

    def test_tasks_without_start_time_ignored(self, sched):
        """Tasks with no start_time set are skipped by conflict detection."""
        t1 = Task("No time A", "walk", duration_minutes=60, priority=1)
        t2 = Task("No time B", "feed", duration_minutes=60, priority=1)
        assert sched.detect_conflicts([t1, t2]) == []

    def test_non_overlapping_tasks_no_conflict(self, sched):
        """Tasks in completely separate time windows return no conflicts."""
        t1 = Task("Morning", "walk", duration_minutes=30, priority=1, start_time="08:00")
        t2 = Task("Evening", "feed", duration_minutes=20, priority=1, start_time="17:00")
        assert sched.detect_conflicts([t1, t2]) == []


# ===========================================================================
# 5. Recurring tasks
# ===========================================================================

class TestRecurringTasks:

    def test_daily_task_next_occurrence_is_tomorrow(self):
        """A daily task's next_occurrence should have due_date = today + 1 day."""
        today = date.today()
        t = Task("Walk", "walk", duration_minutes=30, priority=1,
                 recurrence="daily", due_date=today)
        nxt = t.next_occurrence()
        assert nxt.due_date == today + timedelta(days=1)

    def test_weekly_task_next_occurrence_is_next_week(self):
        """A weekly task's next_occurrence should have due_date = today + 7 days."""
        today = date.today()
        t = Task("Bath", "grooming", duration_minutes=20, priority=2,
                 recurrence="weekly", due_date=today)
        nxt = t.next_occurrence()
        assert nxt.due_date == today + timedelta(weeks=1)

    def test_next_occurrence_starts_incomplete(self):
        """The rescheduled task must always start as not completed."""
        t = Task("Walk", "walk", duration_minutes=30, priority=1,
                 recurrence="daily", due_date=date.today())
        nxt = t.next_occurrence()
        assert nxt.is_completed is False

    def test_next_occurrence_has_no_start_time(self):
        """The rescheduled task should have no start_time — it hasn't been planned yet."""
        t = Task("Walk", "walk", duration_minutes=30, priority=1,
                 recurrence="daily", due_date=date.today(), start_time="08:00")
        nxt = t.next_occurrence()
        assert nxt.start_time == ""

    def test_one_time_task_complete_returns_none(self):
        """complete() on a non-recurring task must return None."""
        t = Task("Vet", "meds", duration_minutes=45, priority=1, recurrence="")
        result = t.complete()
        assert result is None

    def test_recurring_complete_returns_new_task(self):
        """complete() on a recurring task must return a new Task instance."""
        t = Task("Walk", "walk", duration_minutes=30, priority=1,
                 recurrence="daily", due_date=date.today())
        nxt = t.complete()
        assert nxt is not None
        assert isinstance(nxt, Task)

    def test_pet_complete_task_appends_next_occurrence(self):
        """pet.complete_task() on a recurring task must grow the task list by 1."""
        pet = Pet("Mochi", "dog", "Shiba Inu", 3)
        t = Task("Walk", "walk", duration_minutes=30, priority=1,
                 recurrence="daily", due_date=date.today())
        pet.add_task(t)
        before = len(pet.get_tasks())
        pet.complete_task(t)
        assert len(pet.get_tasks()) == before + 1

    def test_pet_complete_task_no_recurrence_does_not_append(self):
        """pet.complete_task() on a one-time task must NOT grow the task list."""
        pet = Pet("Mochi", "dog", "Shiba Inu", 3)
        t = Task("Vet", "meds", duration_minutes=45, priority=1, recurrence="")
        pet.add_task(t)
        before = len(pet.get_tasks())
        pet.complete_task(t)
        assert len(pet.get_tasks()) == before

    def test_next_occurrence_with_no_due_date_defaults_to_today(self):
        """When due_date is None, next_occurrence uses today as the base date."""
        t = Task("Walk", "walk", duration_minutes=30, priority=1,
                 recurrence="daily", due_date=None)
        nxt = t.next_occurrence()
        assert nxt.due_date == date.today() + timedelta(days=1)
