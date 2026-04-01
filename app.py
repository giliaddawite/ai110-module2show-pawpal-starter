import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITY_MAP

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pets" not in st.session_state:
    st.session_state.pets = []
if "task_display" not in st.session_state:
    st.session_state.task_display = {}


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("A smart daily pet care planner — priority scheduling, conflict detection, and recurring tasks.")
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
    owner = Owner(owner_name, available_minutes=int(available_mins))
    pet   = Pet(pet_name, species=species, breed=breed, age=int(age))
    owner.add_pet(pet)
    st.session_state.owner        = owner
    st.session_state.pets         = [pet]
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
        new_pet = Pet(new_pet_name, species=new_species, breed=new_breed, age=int(new_age))
        st.session_state.owner.add_pet(new_pet)
        st.session_state.pets.append(new_pet)
        st.session_state.task_display[new_pet_name] = []
        st.success(f"{new_pet_name} added! "
                   f"Owner now has {len(st.session_state.owner.get_pets())} pet(s).")

st.divider()


# ---------------------------------------------------------------------------
# Section 2 — Add care tasks
# ---------------------------------------------------------------------------
st.subheader("2. Add Care Tasks")

if not st.session_state.pets:
    st.info("Save a profile to unlock task entry.")
else:
    pet_names   = [p.name for p in st.session_state.pets]
    target_name = st.selectbox("Add tasks for:", pet_names, key="task_target")
    target_pet  = next(p for p in st.session_state.pets if p.name == target_name)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        task_name    = st.text_input("Task name", value="Morning walk")
    with col2:
        category     = st.selectbox("Category", ["walk", "feed", "meds", "grooming", "enrichment"])
    with col3:
        duration     = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col4:
        priority_str = st.selectbox("Priority", ["high", "medium", "low"])
    with col5:
        recurrence   = st.selectbox("Recurs?", ["", "daily", "weekly"],
                                    format_func=lambda x: x if x else "one-time")

    if st.button("Add Task"):
        task = Task(
            name=task_name,
            category=category,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority_str],
            recurrence=recurrence,
        )
        target_pet.add_task(task)
        recur_label = f" ({recurrence})" if recurrence else ""
        st.session_state.task_display[target_name].append({
            "Task": task_name,
            "Category": category,
            "Duration (min)": int(duration),
            "Priority": priority_str,
            "Recurs": recurrence if recurrence else "one-time",
        })
        st.success(f"Added '{task_name}' to {target_name}{recur_label}.")

    # ── Task view with filter controls ──────────────────────────────────────
    rows = st.session_state.task_display.get(target_name, [])
    if rows:
        with st.expander(f"View {target_name}'s tasks ({len(rows)})", expanded=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                status_filter = st.selectbox(
                    "Filter by status",
                    ["all", "pending", "done"],
                    key="status_filter",
                )
            with f_col2:
                cat_filter = st.selectbox(
                    "Filter by category",
                    ["all"] + ["walk", "feed", "meds", "grooming", "enrichment"],
                    key="cat_filter",
                )

            # Apply filters using Scheduler.filter_tasks()
            temp_owner = st.session_state.owner
            temp_sched = Scheduler(temp_owner, target_pet)
            all_tasks  = target_pet.get_tasks()

            filtered = temp_sched.filter_tasks(
                all_tasks,
                completed=(None if status_filter == "all" else status_filter == "done"),
                category=(None if cat_filter == "all" else cat_filter),
            )

            if not filtered:
                st.info("No tasks match the selected filters.")
            else:
                display_rows = []
                for t in filtered:
                    recur_icon = "🔁" if t.recurrence else ""
                    display_rows.append({
                        "Task": f"{recur_icon} {t.name}".strip(),
                        "Category": t.category,
                        "Duration (min)": t.duration_minutes,
                        "Priority": {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(t.priority, ""),
                        "Recurs": t.recurrence if t.recurrence else "one-time",
                        "Status": "✅ Done" if t.is_completed else "⏳ Pending",
                    })
                st.dataframe(display_rows, use_container_width=True)
    else:
        st.info(f"No tasks for {target_name} yet.")

st.divider()


# ---------------------------------------------------------------------------
# Section 3 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("3. Generate Today's Schedule")

if not st.session_state.pets:
    st.info("Save a profile to unlock the scheduler.")
else:
    pet_names  = [p.name for p in st.session_state.pets]
    sched_name = st.selectbox("Schedule for:", pet_names, key="sched_target")
    sched_pet  = next(p for p in st.session_state.pets if p.name == sched_name)

    start_hour = st.slider("Day starts at (hour)", min_value=5, max_value=12, value=8,
                           format="%d:00")

    if st.button("Generate Schedule"):
        tasks = sched_pet.get_tasks()
        if not tasks:
            st.warning(f"Add at least one task for {sched_name} first.")
        else:
            scheduler = Scheduler(st.session_state.owner, sched_pet)
            plan      = scheduler.generate_plan(start_hour=start_hour)

            if not plan:
                st.error("No tasks could fit in your available time.")
            else:
                # ── 1. Conflict detection — shown FIRST so owner sees it immediately ──
                sorted_plan = scheduler.sort_by_time(plan)
                conflicts   = scheduler.detect_conflicts(sorted_plan)

                if conflicts:
                    st.warning(
                        f"⚠️ **{len(conflicts)} scheduling conflict(s) detected** — "
                        "the tasks below overlap in time. Consider adjusting durations or start times."
                    )
                    for task_a, task_b in conflicts:
                        st.error(
                            f"🔴 **{task_a.name}** ({task_a.start_time}, {task_a.duration_minutes} min)  "
                            f"overlaps with  **{task_b.name}** ({task_b.start_time}, {task_b.duration_minutes} min)"
                        )
                    st.divider()

                # ── 2. Timed schedule table (sorted chronologically) ─────────────
                st.success(f"Scheduled {len(plan)} task(s) for {sched_name} "
                           f"starting at {start_hour:02d}:00")

                table_rows = []
                for task in sorted_plan:
                    h, m   = divmod(task.duration_minutes, 60)
                    dur_str = f"{h}h {m}m" if h else f"{m}m"
                    recur_icon = " 🔁" if task.recurrence else ""
                    table_rows.append({
                        "Start": task.start_time,
                        "Task": task.name + recur_icon,
                        "Category": task.category,
                        "Duration": dur_str,
                        "Priority": {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(task.priority, ""),
                    })
                st.dataframe(table_rows, use_container_width=True)

                # ── 3. Time summary ──────────────────────────────────────────────
                total     = sum(t.duration_minutes for t in plan)
                remaining = st.session_state.owner.available_minutes - total
                pct_used  = int(total / st.session_state.owner.available_minutes * 100)
                st.progress(pct_used / 100,
                            text=f"{total} min used / {st.session_state.owner.available_minutes} min budget ({remaining} min free)")

                # ── 4. Recurring task callout ────────────────────────────────────
                recurring_in_plan = [t for t in plan if t.recurrence]
                if recurring_in_plan:
                    with st.expander(f"🔁 {len(recurring_in_plan)} recurring task(s) in today's plan"):
                        for t in recurring_in_plan:
                            st.markdown(f"- **{t.name}** repeats `{t.recurrence}` — "
                                        f"completing it will auto-schedule the next occurrence.")

                # ── 5. Skipped tasks ─────────────────────────────────────────────
                skipped = scheduler.get_unscheduled(plan)
                if skipped:
                    with st.expander(f"⏭️ {len(skipped)} task(s) skipped — not enough time"):
                        for t in skipped:
                            badge = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}.get(t.priority, "")
                            st.markdown(f"- **{t.name}** — {t.duration_minutes} min, {badge}")
                else:
                    st.success("All pending tasks fit within your time budget!")
