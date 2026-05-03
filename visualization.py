"""
visualization.py
----------------
All Matplotlib-based drawing routines.

Public API
----------
draw_gantt(gantt, title, parent_frame)
    Embeds a Gantt chart into a Tkinter frame.

draw_comparison_charts(comparison_dict, parent_frame)
    Embeds side-by-side bar charts for avg WT and avg TAT.

DISTINCT_COLORS : list
    Pre-defined palette so each PID always gets the same color.
"""

import matplotlib
matplotlib.use("TkAgg")                         # Must be set before pyplot import

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


# ── Color palette ──────────────────────────────────────────────────────────────
DISTINCT_COLORS = [
    "#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261",
    "#6A0572", "#48CAE4", "#80B918", "#F72585", "#4CC9F0",
    "#7B2D8B", "#FF6B6B", "#06D6A0", "#FFB703", "#8338EC",
    "#3A86FF", "#FB5607", "#8AC926", "#FFBE0B", "#FF006E",
]


def _pid_color_map(gantt_entries: list) -> dict:
    """Assign a stable color to each unique PID."""
    pids = sorted({e.pid for e in gantt_entries})
    return {pid: DISTINCT_COLORS[i % len(DISTINCT_COLORS)] for i, pid in enumerate(pids)}


def _clear_frame(frame):
    """Destroy all child widgets in a Tkinter frame."""
    for widget in frame.winfo_children():
        widget.destroy()


# ── Gantt Chart ────────────────────────────────────────────────────────────────

def draw_gantt(gantt: list, title: str = "Gantt Chart", parent_frame=None) -> FigureCanvasTkAgg:
    """
    Draw a horizontal Gantt chart and embed it in *parent_frame*.

    Parameters
    ----------
    gantt        : list of GanttEntry namedtuples
    title        : chart title string
    parent_frame : Tkinter widget to embed the chart in

    Returns
    -------
    FigureCanvasTkAgg instance (so the caller can keep a reference)
    """
    if parent_frame is not None:
        _clear_frame(parent_frame)

    if not gantt:
        return None

    color_map = _pid_color_map(gantt)
    pids = sorted({e.pid for e in gantt})
    pid_index = {pid: i for i, pid in enumerate(pids)}

    fig, ax = plt.subplots(figsize=(12, max(2.5, len(pids) * 0.8 + 1.5)))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#2A2A3E")

    for entry in gantt:
        y_pos = pid_index[entry.pid]
        width = entry.end - entry.start
        ax.barh(
            y=y_pos,
            width=width,
            left=entry.start,
            height=0.55,
            color=color_map[entry.pid],
            edgecolor="#1E1E2E",
            linewidth=1.2,
        )
        # Label inside bar if wide enough
        if width >= 1:
            ax.text(
                entry.start + width / 2,
                y_pos,
                entry.pid,
                ha="center", va="center",
                fontsize=8, fontweight="bold", color="white",
            )

    # Axis formatting
    max_time = max(e.end for e in gantt)
    ax.set_xlim(0, max_time + 0.5)
    ax.set_xticks(range(0, max_time + 2))
    ax.set_yticks(range(len(pids)))
    ax.set_yticklabels(pids, color="white", fontsize=10)
    ax.set_xlabel("Time", color="white", fontsize=11)
    ax.set_ylabel("Process", color="white", fontsize=11)
    ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555577")

    ax.grid(axis="x", linestyle="--", alpha=0.3, color="white")

    # Legend
    legend_patches = [
        mpatches.Patch(color=color_map[pid], label=pid) for pid in pids
    ]
    ax.legend(
        handles=legend_patches,
        loc="upper right",
        fontsize=8,
        facecolor="#2A2A3E",
        labelcolor="white",
        edgecolor="#555577",
    )

    fig.tight_layout()

    if parent_frame is not None:
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)
        return canvas

    plt.show()
    return None


# ── Comparison Bar Charts ──────────────────────────────────────────────────────

def draw_comparison_charts(comparison: dict, parent_frame=None) -> FigureCanvasTkAgg:
    """
    Draw two side-by-side bar charts comparing algorithms by avg WT and avg TAT.

    Parameters
    ----------
    comparison   : dict  {algorithm_name: metrics_dict}
    parent_frame : Tkinter widget to embed the chart in
    """
    if parent_frame is not None:
        _clear_frame(parent_frame)

    if not comparison:
        return None

    names   = list(comparison.keys())
    avg_wts = [comparison[n]["avg_wt"]  for n in names]
    avg_tats= [comparison[n]["avg_tat"] for n in names]

    x     = np.arange(len(names))
    width = 0.35
    bar_colors_wt  = ["#E63946", "#F4A261", "#2A9D8F"][:len(names)]
    bar_colors_tat = ["#457B9D", "#E9C46A", "#6A0572"][:len(names)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#1E1E2E")

    def _style_ax(ax, title, ylabel, values, colors):
        ax.set_facecolor("#2A2A3E")
        bars = ax.bar(x, values, width=0.5, color=colors, edgecolor="#1E1E2E", linewidth=1.2)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3,
                f"{val:.2f}",
                ha="center", va="bottom",
                color="white", fontsize=10, fontweight="bold",
            )
        ax.set_xticks(x)
        ax.set_xticklabels(names, color="white", fontsize=9, rotation=10, ha="right")
        ax.set_ylabel(ylabel, color="white", fontsize=11)
        ax.set_title(title, color="white", fontsize=12, fontweight="bold", pad=10)
        ax.tick_params(colors="white")
        ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="white")
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_edgecolor("#555577")
        ax.set_ylim(0, max(values) * 1.3 + 1)

    _style_ax(ax1, "Average Waiting Time",     "Avg WT (ms)",  avg_wts,  bar_colors_wt)
    _style_ax(ax2, "Average Turnaround Time",  "Avg TAT (ms)", avg_tats, bar_colors_tat)

    fig.tight_layout(pad=3)

    if parent_frame is not None:
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)
        return canvas

    plt.show()
    return None
