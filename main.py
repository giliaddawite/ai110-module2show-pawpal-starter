"""
main.py
-------
Demo script for PawPal+.
Verifies backend logic end-to-end in the terminal before connecting the UI.
"""

from pawpal_system import Task, Pet, Owner, Scheduler, PRIORITY_MAP


# ---------------------------------------------------------------------------
# 1. Set up the owner
# ---------------------------------------------------------------------------
owner = Owner("Jordan", available_minutes=120)

# ---------------------------------------------------------------------------
# 2. Create two pets and register them
# ---------------------------------------------------------------------------
mochi = Pet("Mochi", species="dog", breed="Shiba Inu", age=3)
luna  = Pet("Luna",  species="cat", breed="Maine Coon", age=5, special_needs=["joint supplement"])

owner.add_pet(mochi)
owner.add_pet(luna)

# ---------------------------------------------------------------------------
# 3. Add tasks for Mochi
# ---------------------------------------------------------------------------
mochi.add_task(Task("Morning walk",     "walk",       duration_minutes=30, priority=PRIORITY_MAP["high"]))
mochi.add_task(Task("Breakfast",        "feed",       duration_minutes=10, priority=PRIORITY_MAP["high"]))
mochi.add_task(Task("Flea medication",  "meds",       duration_minutes=5,  priority=PRIORITY_MAP["high"]))
mochi.add_task(Task("Fetch session",    "enrichment", duration_minutes=20, priority=PRIORITY_MAP["medium"]))
mochi.add_task(Task("Brush coat",       "grooming",   duration_minutes=15, priority=PRIORITY_MAP["medium"]))
mochi.add_task(Task("Agility practice", "enrichment", duration_minutes=45, priority=PRIORITY_MAP["low"]))

# ---------------------------------------------------------------------------
# 4. Add tasks for Luna
# ---------------------------------------------------------------------------
luna.add_task(Task("Joint supplement",  "meds",       duration_minutes=5,  priority=PRIORITY_MAP["high"]))
luna.add_task(Task("Breakfast",         "feed",       duration_minutes=10, priority=PRIORITY_MAP["high"]))
luna.add_task(Task("Laser pointer play","enrichment", duration_minutes=15, priority=PRIORITY_MAP["medium"]))
luna.add_task(Task("Brush fur",         "grooming",   duration_minutes=10, priority=PRIORITY_MAP["low"]))

# ---------------------------------------------------------------------------
# 5. Generate and print today's schedule for each pet
# ---------------------------------------------------------------------------
DIVIDER = "=" * 52

def print_schedule(owner: Owner, pet: Pet) -> None:
    scheduler = Scheduler(owner, pet)
    plan      = scheduler.generate_plan()
    print(scheduler.explain_plan(plan))


print()
print(DIVIDER)
print(f"  PawPal+ — Today's Schedule for {owner.name}")
print(DIVIDER)

for pet in owner.get_pets():
    print()
    print_schedule(owner, pet)
    print()

print(DIVIDER)
print(f"  All registered pets: {', '.join(p.name for p in owner.get_pets())}")
print(f"  Total tasks across all pets: {len(owner.get_all_tasks())}")
print(DIVIDER)
print()
