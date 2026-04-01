"""
main.py
-------
Demo script for PawPal+.
Verifies backend logic — sorting, filtering, recurring tasks, conflict detection.
"""

from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler, PRIORITY_MAP

DIVIDER = "=" * 52

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner("Jordan", available_minutes=120)

mochi = Pet("Mochi", species="dog", breed="Shiba Inu", age=3)
luna  = Pet("Luna",  species="cat", breed="Maine Coon", age=5,
            special_needs=["joint supplement"])

owner.add_pet(mochi)
owner.add_pet(luna)

# Tasks added intentionally OUT OF ORDER (priority and time mixed up)
# so sort_by_time() and generate_plan() have something interesting to do.
mochi.add_task(Task("Agility practice", "enrichment", duration_minutes=45,
                    priority=PRIORITY_MAP["low"],    recurrence="weekly"))
mochi.add_task(Task("Breakfast",        "feed",       duration_minutes=10,
                    priority=PRIORITY_MAP["high"],   recurrence="daily"))
mochi.add_task(Task("Fetch session",    "enrichment", duration_minutes=20,
                    priority=PRIORITY_MAP["medium"]))
mochi.add_task(Task("Flea medication",  "meds",       duration_minutes=5,
                    priority=PRIORITY_MAP["high"],   recurrence="daily"))
mochi.add_task(Task("Morning walk",     "walk",       duration_minutes=30,
                    priority=PRIORITY_MAP["high"],   recurrence="daily"))
mochi.add_task(Task("Brush coat",       "grooming",   duration_minutes=15,
                    priority=PRIORITY_MAP["medium"]))

luna.add_task(Task("Laser pointer play","enrichment", duration_minutes=15,
                   priority=PRIORITY_MAP["medium"]))
luna.add_task(Task("Joint supplement",  "meds",       duration_minutes=5,
                   priority=PRIORITY_MAP["high"],    recurrence="daily"))
luna.add_task(Task("Brush fur",         "grooming",   duration_minutes=10,
                   priority=PRIORITY_MAP["low"]))
luna.add_task(Task("Breakfast",         "feed",       duration_minutes=10,
                   priority=PRIORITY_MAP["high"],    recurrence="daily"))


# ---------------------------------------------------------------------------
# 1. Generate schedule (priority-sorted + auto-timed)
# ---------------------------------------------------------------------------
print()
print(DIVIDER)
print("  PawPal+ — Today's Schedule")
print(DIVIDER)

for pet in owner.get_pets():
    scheduler = Scheduler(owner, pet)
    plan      = scheduler.generate_plan(start_hour=8)   # day starts at 08:00
    print()
    print(scheduler.explain_plan(plan))
    print()


# ---------------------------------------------------------------------------
# 2. Sort by time  (demonstrates sort_by_time + lambda key)
# ---------------------------------------------------------------------------
print(DIVIDER)
print("  Sort-by-time demo — Mochi's plan after generate_plan()")
print(DIVIDER)

sched = Scheduler(owner, mochi)
plan  = sched.generate_plan(start_hour=8)

sorted_tasks = sched.sort_by_time(plan)
print("\n  Tasks in chronological order:")
for t in sorted_tasks:
    print(f"    {t.start_time}  {t.name} ({t.duration_minutes} min)")


# ---------------------------------------------------------------------------
# 3. Filter by status and category
# ---------------------------------------------------------------------------
print()
print(DIVIDER)
print("  Filter demo — Mochi's tasks")
print(DIVIDER)

sched = Scheduler(owner, mochi)
all_tasks = sched.tasks

# Mark one task complete to make the filter demo meaningful
all_tasks[1].complete()   # mark Breakfast as done

pending  = sched.filter_tasks(all_tasks, completed=False)
done     = sched.filter_tasks(all_tasks, completed=True)
walks    = sched.filter_tasks(all_tasks, category="walk")
hi_pend  = sched.filter_tasks(all_tasks, completed=False, category="meds")

print(f"\n  Pending tasks  ({len(pending)}): {[t.name for t in pending]}")
print(f"  Done tasks     ({len(done)}):    {[t.name for t in done]}")
print(f"  Walk tasks     ({len(walks)}):   {[t.name for t in walks]}")
print(f"  Pending meds   ({len(hi_pend)}): {[t.name for t in hi_pend]}")


# ---------------------------------------------------------------------------
# 4. Recurring tasks
# ---------------------------------------------------------------------------
print()
print(DIVIDER)
print("  Recurring tasks demo")
print(DIVIDER)

for pet in owner.get_pets():
    s         = Scheduler(owner, pet)
    recurring = s.get_recurring()
    print(f"\n  {pet.name}'s recurring tasks ({len(recurring)}):")
    for t in recurring:
        print(f"    [{t.recurrence:7s}]  {t.name}")


# ---------------------------------------------------------------------------
# 5. Conflict detection
# ---------------------------------------------------------------------------
print()
print(DIVIDER)
print("  Conflict detection demo")
print(DIVIDER)

# Manually create two tasks with overlapping times to trigger a conflict
conflict_pet = Pet("Rex", "dog", "Lab", 2)
t1 = Task("Vet appointment", "meds",  duration_minutes=45, priority=1, start_time="09:00")
t2 = Task("Morning walk",    "walk",  duration_minutes=30, priority=1, start_time="09:20")  # overlaps t1
t3 = Task("Breakfast",       "feed",  duration_minutes=10, priority=1, start_time="10:00")  # no conflict
conflict_pet.add_task(t1)
conflict_pet.add_task(t2)
conflict_pet.add_task(t3)
owner.add_pet(conflict_pet)

s_conflict = Scheduler(owner, conflict_pet)
conflicts  = s_conflict.detect_conflicts(conflict_pet.get_tasks())

if conflicts:
    print(f"\n  {len(conflicts)} conflict(s) found:")
    for a, b in conflicts:
        print(f"    '{a.name}' ({a.start_time}, {a.duration_minutes}min)"
              f"  overlaps  '{b.name}' ({b.start_time}, {b.duration_minutes}min)")
else:
    print("\n  No conflicts detected.")

# No-conflict check
no_conflict_tasks = [t1, t3]                    # t1 ends at 09:45, t3 starts at 10:00
nc = s_conflict.detect_conflicts(no_conflict_tasks)
print(f"\n  [t1, t3] only — conflicts: {len(nc)} (expected 0)")

# ---------------------------------------------------------------------------
# 6. Recurring task auto-rescheduling
# ---------------------------------------------------------------------------
print()
print(DIVIDER)
print("  Recurring task auto-rescheduling demo")
print(DIVIDER)

# Set explicit due dates so the output is deterministic
today = date.today()
morning_walk   = Task("Morning walk", "walk",  duration_minutes=30,
                      priority=PRIORITY_MAP["high"], recurrence="daily",  due_date=today)
weekly_groom   = Task("Bath time",    "grooming", duration_minutes=20,
                      priority=PRIORITY_MAP["medium"], recurrence="weekly", due_date=today)
one_time_vet   = Task("Vet checkup",  "meds",  duration_minutes=45,
                      priority=PRIORITY_MAP["high"], recurrence="")   # no recurrence

demo_pet = Pet("Demo", "dog", "Mixed", 2)
demo_pet.add_task(morning_walk)
demo_pet.add_task(weekly_groom)
demo_pet.add_task(one_time_vet)

print(f"\n  Tasks BEFORE completing anything ({len(demo_pet.get_tasks())}):")
for t in demo_pet.get_tasks():
    print(f"    {t.name:20s}  due={t.due_date}  recurrence='{t.recurrence}'  done={t.is_completed}")

# Complete all three tasks
next1 = demo_pet.complete_task(morning_walk)   # daily  → should create tomorrow's task
next2 = demo_pet.complete_task(weekly_groom)   # weekly → should create next-week's task
next3 = demo_pet.complete_task(one_time_vet)   # none   → should return None

print(f"\n  complete_task(morning_walk) returned: {next1}")
print(f"  complete_task(weekly_groom) returned: {next2}")
print(f"  complete_task(one_time_vet) returned: {next3}  (None = no recurrence)")

print(f"\n  Tasks AFTER completing all three ({len(demo_pet.get_tasks())}):")
for t in demo_pet.get_tasks():
    status = "DONE" if t.is_completed else "pending"
    print(f"    {t.name:20s}  due={t.due_date}  recurrence='{t.recurrence}'  [{status}]")

print()
print(DIVIDER)
print(f"  Total pets: {len(owner.get_pets())}")
print(f"  Total tasks across all pets: {len(owner.get_all_tasks())}")
print(DIVIDER)
print()
