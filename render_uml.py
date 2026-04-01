"""
render_uml.py
-------------
Generates uml_final.png — a class diagram matching the final pawpal_system.py.
Run once: python render_uml.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
FIG_W, FIG_H = 18, 13
HDR_COLOR  = "#2C3E50"     # dark blue-grey for class name band
BODY_COLOR = "#ECF0F1"     # light grey for attributes / methods
BORDER     = "#2C3E50"
TEXT_WHITE = "white"
TEXT_DARK  = "#2C3E50"
FONT_NAME  = "monospace"

# ---------------------------------------------------------------------------
# Class box data  [x, y, width, height]
# Each entry: (label, [(attr_lines), (method_lines)], box_rect)
# ---------------------------------------------------------------------------
CLASSES = [
    {
        "name": "Task",
        "attrs": [
            "+ name : str",
            "+ category : str",
            "+ duration_minutes : int",
            "+ priority : int",
            "+ is_completed : bool",
            "+ start_time : str",
            "+ recurrence : str",
            "+ due_date : date",
        ],
        "methods": [
            "+ complete() → Optional[Task]",
            "+ next_occurrence() → Task",
        ],
        "box": (0.05, 0.52, 0.27, 0.44),
    },
    {
        "name": "Pet",
        "attrs": [
            "+ name : str",
            "+ species : str",
            "+ breed : str",
            "+ age : int",
            "+ special_needs : list[str]",
            "- _tasks : list[Task]",
        ],
        "methods": [
            "+ add_task(task)",
            "+ complete_task(task) → Optional[Task]",
            "+ get_tasks() → list[Task]",
        ],
        "box": (0.37, 0.52, 0.27, 0.44),
    },
    {
        "name": "Owner",
        "attrs": [
            "+ name : str",
            "+ available_minutes : int",
            "+ preferences : dict",
            "- _pets : list[Pet]",
        ],
        "methods": [
            "+ add_pet(pet)",
            "+ get_pets() → list[Pet]",
            "+ get_all_tasks() → list[Task]",
        ],
        "box": (0.69, 0.52, 0.27, 0.44),
    },
    {
        "name": "Scheduler",
        "attrs": [
            "+ owner : Owner",
            "+ pet : Pet",
            "+ tasks : list[Task]",
        ],
        "methods": [
            "+ generate_plan(start_hour) → list[Task]",
            "+ explain_plan(plan) → str",
            "+ get_unscheduled(plan) → list[Task]",
            "+ sort_by_time(tasks) → list[Task]",
            "+ filter_tasks(tasks, …) → list[Task]",
            "+ get_recurring() → list[Task]",
            "+ assign_start_times(plan, start_hour)",
            "+ detect_conflicts(tasks) → list[tuple]",
        ],
        "box": (0.21, 0.01, 0.58, 0.44),
    },
]

# ---------------------------------------------------------------------------
# Relationships  (start_xy, end_xy, label, style)
# style: "solid" = composition/association, "dashed" = dependency
# ---------------------------------------------------------------------------
RELATIONS = [
    # Owner "1" --> "*" Pet
    dict(
        start=(0.69 + 0.135, 0.52 + 0.22),   # mid-left of Owner
        end  =(0.37 + 0.27,  0.52 + 0.22),   # mid-right of Pet
        label='Owner "1" ──▶ "*" Pet\nhas',
        style="solid",
    ),
    # Pet "1" --> "*" Task
    dict(
        start=(0.37 + 0.135, 0.52 + 0.22),
        end  =(0.05 + 0.27,  0.52 + 0.22),
        label='Pet "1" ──▶ "*" Task\nowns',
        style="solid",
    ),
    # Scheduler --> Owner  (reads budget)
    dict(
        start=(0.21 + 0.58,  0.01 + 0.22),   # mid-right of Scheduler
        end  =(0.69 + 0.135, 0.52),           # bottom-mid of Owner
        label="reads budget",
        style="dashed",
    ),
    # Scheduler --> Pet  (snapshots tasks)
    dict(
        start=(0.21 + 0.29,  0.01 + 0.44),   # top-mid of Scheduler
        end  =(0.37 + 0.135, 0.52),           # bottom-mid of Pet
        label="snapshots\ntasks",
        style="dashed",
    ),
    # Task ..> Task  (next_occurrence creates)
    dict(
        start=(0.05,         0.52 + 0.38),
        end  =(0.05,         0.52 + 0.44),
        label="next_occurrence()\ncreates new Task",
        style="self",
    ),
]

# ---------------------------------------------------------------------------
# Draw
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.patch.set_facecolor("white")

LINE_H = 0.024   # height of one text line inside a box

def draw_class(ax, cls):
    x, y, w, h = cls["box"]
    n_attrs   = len(cls["attrs"])
    n_methods = len(cls["methods"])

    # header band height
    hdr_h    = LINE_H * 1.8
    attr_h   = LINE_H * (n_attrs  + 0.5)
    meth_h   = LINE_H * (n_methods + 0.5)
    total_h  = hdr_h + attr_h + meth_h

    # --- header ---
    hdr = mpatches.FancyBboxPatch(
        (x, y + h - hdr_h), w, hdr_h,
        boxstyle="square,pad=0",
        linewidth=1.5, edgecolor=BORDER, facecolor=HDR_COLOR,
        transform=ax.transAxes, zorder=3,
    )
    ax.add_patch(hdr)
    ax.text(x + w / 2, y + h - hdr_h / 2, f"«class»\n{cls['name']}",
            ha="center", va="center", fontsize=9, fontweight="bold",
            color=TEXT_WHITE, fontfamily=FONT_NAME,
            transform=ax.transAxes, zorder=4)

    # --- attributes section ---
    attr_top = y + h - hdr_h
    attr_box = mpatches.FancyBboxPatch(
        (x, attr_top - attr_h), w, attr_h,
        boxstyle="square,pad=0",
        linewidth=1.5, edgecolor=BORDER, facecolor=BODY_COLOR,
        transform=ax.transAxes, zorder=3,
    )
    ax.add_patch(attr_box)
    for i, line in enumerate(cls["attrs"]):
        ty = attr_top - LINE_H * 0.6 - LINE_H * i
        ax.text(x + 0.008, ty, line,
                ha="left", va="top", fontsize=7,
                color=TEXT_DARK, fontfamily=FONT_NAME,
                transform=ax.transAxes, zorder=4)

    # --- methods section ---
    meth_top = attr_top - attr_h
    meth_box = mpatches.FancyBboxPatch(
        (x, meth_top - meth_h), w, meth_h,
        boxstyle="square,pad=0",
        linewidth=1.5, edgecolor=BORDER, facecolor="white",
        transform=ax.transAxes, zorder=3,
    )
    ax.add_patch(meth_box)
    for i, line in enumerate(cls["methods"]):
        ty = meth_top - LINE_H * 0.6 - LINE_H * i
        ax.text(x + 0.008, ty, line,
                ha="left", va="top", fontsize=7,
                color="#1A5276", fontfamily=FONT_NAME, fontstyle="italic",
                transform=ax.transAxes, zorder=4)

for cls in CLASSES:
    draw_class(ax, cls)

# ---------------------------------------------------------------------------
# Draw relationships
# ---------------------------------------------------------------------------
for rel in RELATIONS:
    sx, sy = rel["start"]
    ex, ey = rel["end"]

    if rel["style"] == "self":
        # self-referencing loop for Task → Task
        ax.annotate(
            "", xy=(ex - 0.04, ey), xytext=(sx - 0.04, sy),
            xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=dict(arrowstyle="->", color="#7D3C98",
                            lw=1.4, linestyle="dashed",
                            connectionstyle="arc3,rad=0.6"),
            zorder=5,
        )
        ax.text(sx - 0.085, (sy + ey) / 2, rel["label"],
                ha="center", va="center", fontsize=6.5,
                color="#7D3C98", fontfamily=FONT_NAME,
                transform=ax.transAxes, zorder=6)
        continue

    ls = "dashed" if rel["style"] == "dashed" else "solid"
    color = "#1A5276" if rel["style"] == "dashed" else "#2C3E50"
    ax.annotate(
        "", xy=(ex, ey), xytext=(sx, sy),
        xycoords="axes fraction", textcoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color=color,
                        lw=1.6, linestyle=ls,
                        mutation_scale=14),
        zorder=5,
    )
    mx, my = (sx + ex) / 2, (sy + ey) / 2 + 0.02
    ax.text(mx, my, rel["label"],
            ha="center", va="bottom", fontsize=6.5,
            color=color, fontfamily=FONT_NAME,
            transform=ax.transAxes, zorder=6,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1))

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
ax.text(0.5, 0.985, "PawPal+  —  Final Class Diagram",
        ha="center", va="top", fontsize=13, fontweight="bold",
        color=HDR_COLOR, transform=ax.transAxes)

plt.tight_layout(pad=0.2)
plt.savefig("uml_final.png", dpi=150, bbox_inches="tight", facecolor="white")
print("Saved: uml_final.png")
