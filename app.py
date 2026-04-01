import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITY_MAP

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session-state initialisation
#
# Streamlit reruns this script top-to-bottom on every interaction.
# Each key is initialised exactly once; subsequent reruns skip the `if`.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None          # Owner instance

if "pets" not in st.session_state:
    st.session_state.pets = []             # list[Pet] — all pets for this owner

if "task_display" not in st.session_state:
    st.session_state.task_display = {}     # dict[pet_name -> list[dict]] for st.table


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("A daily pet care planner that fits tasks into your available time.")
st.divider()


# ---------------------------------------------------------------------------
# Section 1 — Owner profile + first pet
# ---------------------------------------------------------------------------
st.subheader("1. Owner & First Pet")

col_a, col_b = st.columns(2)
with col_a:
    owner_name     = st.text_input("Your name", value="Jordan")
    available_mins = st.number_input("Daily time budget (minutes)",
                                     min_value=10, max_value=480, value=90, step=10)
with col_b:
    pet_name = st.text_input("Pet name", value="Mochi")
    species  = st.selectbox("Species", ["dog", "cat", "other"])
    breed    = st.text_input("Breed", value="Shiba Inu")
    age      = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

if st.button("Save Profile"):
    # ── UI action: "save profile"
    # ── Backend: Owner.__init__()  +  Pet.__init__()  +  owner.add_pet()
    owner = Owner(owner_name, available_minutes=int(available_mins))
    pet   = Pet(pet_name, species=species, breed=breed, age=int(age))
    owner.add_pet(pet)                     # <-- Owner.add_pet() registers the pet

    st.session_state.owner        = owner
    st.session_state.pets         = [pet]  # UI now knows about this pet
    st.session_state.task_display = {pet_name: []}
    st.success(f"Profile saved — {owner_name} & {pet_name} are ready!")

if st.session_state.owner:
    st.info(
        f"Owner: **{st.session_state.owner.name}** "
        f"| Budget: {st.session_state.owner.available_minutes} min/day "
        f"| Pets: {', '.join(p.name for p in st.session_state.pets)}"
    )

st.divider()


# ---------------------------------------------------------------------------
# Section 1b — Add another pet
# ---------------------------------------------------------------------------
st.subheader("1b. Add Another Pet")
st.caption("owner.add_pet() registers each new pet under the same owner.")

with st.form("add_pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        new_pet_name = st.text_input("Pet name", value="Luna")
        new_species  = st.selectbox("Species", ["dog", "cat", "other"], key="new_species")
    with col2:
        new_breed = st.text_input("Breed", value="Maine Coon")
        new_age   = st.number_input("Age (years)", min_value=0, max_value=30, value=2, key="new_age")
    submitted = st.form_submit_button("Add Pet")

if submitted:
    if st.session_state.owner is None:
        st.warning("Save an owner profile first.")
    elif any(p.name == new_pet_name for p in st.session_state.pets):
        st.warning(f"A pet named '{new_pet_name}' already exists.")
    else:
        # ── UI action: "add another pet"
        # ── Backend: Pet.__init__()  +  owner.add_pet()
        new_pet = Pet(new_pet_name, species=new_species, breed=new_breed, age=int(new_age))
        st.session_state.owner.add_pet(new_pet)      # <-- owner.add_pet() is the bridge
        st.session_state.pets.append(new_pet)        # UI mirror updated to show the change
        st.session_state.task_display[new_pet_name] = []
        st.success(f"{new_pet_name} added! Owner now has "
                   f"{len(st.session_state.owner.get_pets())} pet(s).")

st.divider()


# ---------------------------------------------------------------------------
# Section 2 — Add care tasks (to a chosen pet)
# ---------------------------------------------------------------------------
st.subheader("2. Add Care Tasks")

if not st.session_state.pets:
    st.info("Save a profile to unlock task entry.")
else:
    pet_names    = [p.name for p in st.session_state.pets]
    target_name  = st.selectbox("Add tasks for:", pet_names, key="task_target")
    # Resolve the UI selection back to the actual Pet object
    # ── UI selection → backend object lookup
    target_pet   = next(p for p in st.session_state.pets if p.name == target_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_name    = st.text_input("Task name", value="Morning walk")
    with col2:
        category     = st.selectbox("Category", ["walk", "feed", "meds", "grooming", "enrichment"])
    with col3:
        duration     = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col4:
        priority_str = st.selectbox("Priority", ["high", "medium", "low"])

    if st.button("Add Task"):
        # ── UI action: "add task"
        # ── Backend: Task.__init__()  +  pet.add_task()
        task = Task(
            name=task_name,
            category=category,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_str],
        )
        target_pet.add_task(task)                    # <-- Pet.add_task() does the real work
        st.session_state.task_display[target_name].append({
            "Task": task_name,
            "Category": category,
            "Duration (min)": int(duration),
            "Priority": priority_str,
        })
        st.success(f"Added '{task_name}' to {target_name}.")

    rows = st.session_state.task_display.get(target_name, [])
    if rows:
        st.write(f"**{target_name}'s tasks ({len(rows)}):**")
        st.table(rows)
    else:
        st.info(f"No tasks for {target_name} yet.")

st.divider()


# ---------------------------------------------------------------------------
# Section 3 — Generate schedule (for a chosen pet)
# ---------------------------------------------------------------------------
st.subheader("3. Generate Today's Schedule")

if not st.session_state.pets:
    st.info("Save a profile to unlock the scheduler.")
else:
    pet_names    = [p.name for p in st.session_state.pets]
    sched_name   = st.selectbox("Schedule for:", pet_names, key="sched_target")
    # Resolve selection → Pet object (same pattern as Section 2)
    sched_pet    = next(p for p in st.session_state.pets if p.name == sched_name)

    if st.button("Generate Schedule"):
        tasks = sched_pet.get_tasks()
        if not tasks:
            st.warning(f"Add at least one task for {sched_name} first.")
        else:
            # ── UI action: "generate schedule"
            # ── Backend: Scheduler.__init__()  +  generate_plan()  +  explain_plan()
            scheduler = Scheduler(st.session_state.owner, sched_pet)
            plan      = scheduler.generate_plan()

            if not plan:
                st.error("No tasks could fit in your available time.")
            else:
                st.success(f"Scheduled {len(plan)} task(s) for {sched_name}!")

                for i, task in enumerate(plan, 1):
                    badge = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(task.priority, "")
                    st.markdown(
                        f"**{i}. {task.name}** &nbsp;|&nbsp; "
                        f"`{task.category}` &nbsp;|&nbsp; "
                        f"{task.duration_minutes} min &nbsp;|&nbsp; {badge}"
                    )

                total     = sum(t.duration_minutes for t in plan)
                remaining = st.session_state.owner.available_minutes - total
                st.markdown(
                    f"\n**Time used:** {total} min / "
                    f"{st.session_state.owner.available_minutes} min available "
                    f"({remaining} min unused)"
                )

                skipped = scheduler.get_unscheduled(plan)
                if skipped:
                    with st.expander(f"⚠️ {len(skipped)} task(s) skipped — not enough time"):
                        for task in skipped:
                            st.markdown(f"- **{task.name}** ({task.duration_minutes} min)")
