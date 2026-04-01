"""
tests/test_pawpal.py
--------------------
Unit tests for PawPal+ core logic.
"""

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, PRIORITY_MAP


# ---------------------------------------------------------------------------
# Fixtures — reusable objects shared across tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    return Task("Morning walk", "walk", duration_minutes=30, priority=PRIORITY_MAP["high"])


@pytest.fixture
def sample_pet():
    return Pet("Mochi", species="dog", breed="Shiba Inu", age=3)


@pytest.fixture
def sample_owner():
    return Owner("Jordan", available_minutes=90)


# ---------------------------------------------------------------------------
# Test 1: Task completion
# ---------------------------------------------------------------------------

def test_task_starts_incomplete(sample_task):
    """A newly created task should not be marked complete."""
    assert sample_task.is_completed is False


def test_complete_marks_task_done(sample_task):
    """Calling complete() should set is_completed to True."""
    sample_task.complete()
    assert sample_task.is_completed is True


# ---------------------------------------------------------------------------
# Test 2: Task addition to a Pet
# ---------------------------------------------------------------------------

def test_adding_task_increases_count(sample_pet, sample_task):
    """Adding a task to a pet should increase its task count by 1."""
    before = len(sample_pet.get_tasks())
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == before + 1


def test_added_task_is_retrievable(sample_pet, sample_task):
    """The task added to a pet should appear in get_tasks()."""
    sample_pet.add_task(sample_task)
    assert sample_task in sample_pet.get_tasks()


# ---------------------------------------------------------------------------
# Bonus: Scheduler respects time budget
# ---------------------------------------------------------------------------

def test_scheduler_does_not_exceed_budget(sample_owner, sample_pet):
    """Scheduled tasks must not exceed the owner's available minutes."""
    sample_pet.add_task(Task("Walk",    "walk",       duration_minutes=30, priority=PRIORITY_MAP["high"]))
    sample_pet.add_task(Task("Feed",    "feed",       duration_minutes=10, priority=PRIORITY_MAP["high"]))
    sample_pet.add_task(Task("Groom",   "grooming",   duration_minutes=60, priority=PRIORITY_MAP["low"]))
    sample_owner.add_pet(sample_pet)

    scheduler = Scheduler(sample_owner, sample_pet)
    plan = scheduler.generate_plan()

    total = sum(t.duration_minutes for t in plan)
    assert total <= sample_owner.available_minutes


def test_scheduler_excludes_completed_tasks(sample_owner, sample_pet):
    """Tasks already marked complete should not appear in the plan."""
    done_task = Task("Old walk", "walk", duration_minutes=20, priority=PRIORITY_MAP["high"])
    done_task.complete()
    sample_pet.add_task(done_task)
    sample_owner.add_pet(sample_pet)

    scheduler = Scheduler(sample_owner, sample_pet)
    plan = scheduler.generate_plan()

    assert done_task not in plan
