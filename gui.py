"""
gui.py
------
Main Tkinter GUI for the Smart CPU Scheduling Simulator.

Tabs
----
  1. Input & Simulation  – add processes, choose algorithm, run
  2. Gantt Chart         – rendered Matplotlib chart
  3. Metrics Table       – per-process WT / TAT table
  4. Algorithm Comparison – run all algorithms, bar charts + table
  5. AI Recommendation   – intelligent algorithm suggester

Layout colours follow a dark-mode palette for readability.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os

# ── Project modules ────────────────────────────────────────────────────────────
from scheduling_algorithms import make_process, fcfs, sjf, round_robin
from metrics import compute_metrics, compare_algorithms
from visualization import draw_gantt, draw_comparison_charts, DISTINCT_COLORS
from ai_recommendation import recommend

# ── Colour palette ─────────────────────────────────────────────────────────────
BG       = "#1E1E2E"
SURFACE  = "#2A2A3E"
ACCENT   = "#7C3AED"
ACCENT2  = "#06D6A0"
TEXT     = "#E2E8F0"
TEXT_DIM = "#94A3B8"
ENTRY_BG = "#353550"
RED      = "#E63946"
GREEN    = "#2A9D8F"

FONT_H1  = ("Segoe UI", 14, "bold")
FONT_H2  = ("Segoe UI", 11, "bold")
FONT_BODY= ("Segoe UI", 10)
FONT_SM  = ("Segoe UI", 9)


# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.title("Smart CPU Scheduling System — AI Optimised")
        self.geometry("1180x780")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._setup_style()

        # State
        self.processes      = []       # list of Process namedtuples
        self.last_gantt     = []
        self.last_metrics   = {}
        self.last_algo      = ""
        self.canvas_gantt   = None
        self.canvas_compare = None

        self._build_header()
        self._build_notebook()

    # ── Style ──────────────────────────────────────────────────────────────────
    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook",          background=BG,      borderwidth=0)
        style.configure("TNotebook.Tab",      background=SURFACE,  foreground=TEXT_DIM,
                        padding=[14, 6],      font=FONT_SM)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        style.configure("TFrame",             background=BG)
        style.configure("Inner.TFrame",       background=SURFACE)
        style.configure("TLabel",             background=BG,      foreground=TEXT,
                        font=FONT_BODY)
        style.configure("Dim.TLabel",         background=BG,      foreground=TEXT_DIM,
                        font=FONT_SM)
        style.configure("H1.TLabel",          background=BG,      foreground=TEXT,
                        font=FONT_H1)
        style.configure("H2.TLabel",          background=SURFACE, foreground=TEXT,
                        font=FONT_H2)
        style.configure("Surface.TLabel",     background=SURFACE, foreground=TEXT,
                        font=FONT_BODY)
        style.configure("Accent.TLabel",      background=BG,      foreground=ACCENT2,
                        font=FONT_H2)

        style.configure("Treeview",           background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE, rowheight=26, font=FONT_BODY)
        style.configure("Treeview.Heading",   background=ACCENT,  foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        style.configure("Horizontal.TScrollbar", background=SURFACE, troughcolor=BG)
        style.configure("Vertical.TScrollbar",   background=SURFACE, troughcolor=BG)

    # ── Header bar ─────────────────────────────────────────────────────────────
    def _build_header(self):
        bar = tk.Frame(self, bg=ACCENT, height=54)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        tk.Label(bar, text="⚙  Smart CPU Scheduling Simulator",
                 bg=ACCENT, fg="white", font=("Segoe UI", 15, "bold")).pack(
            side="left", padx=20, pady=10)
        tk.Label(bar, text="AI-Optimised · Multi-Algorithm · Visual",
                 bg=ACCENT, fg="#C4B5FD", font=FONT_SM).pack(
            side="right", padx=20)

    # ── Notebook tabs ──────────────────────────────────────────────────────────
    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        tabs = [
            ("  🖊  Input & Run  ",    self._tab_input),
            ("  📊  Gantt Chart  ",    self._tab_gantt),
            ("  📋  Metrics  ",        self._tab_metrics),
            ("  🔀  Compare  ",        self._tab_compare),
            ("  🤖  AI Suggest  ",     self._tab_ai),
        ]

        self.tab_frames = {}
        for label, builder in tabs:
            frame = ttk.Frame(self.nb)
            self.nb.add(frame, text=label)
            self.tab_frames[label] = frame
            builder(frame)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Input & Run
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_input(self, parent):
        parent.configure(style="TFrame")

        # ── Left panel: process entry form ────────────────────────────────────
        left = tk.Frame(parent, bg=SURFACE, bd=0, relief="flat", width=310)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        left.pack_propagate(False)

        tk.Label(left, text="Add Process", bg=SURFACE, fg=TEXT,
                 font=FONT_H2).pack(pady=(14, 6), padx=14, anchor="w")

        fields = [
            ("Process ID",   "pid",     "P1"),
            ("Arrival Time", "arrival", "0"),
            ("Burst Time",   "burst",   "5"),
            ("Priority",     "priority","0  (optional)"),
        ]
        self._entries = {}
        for label, key, placeholder in fields:
            tk.Label(left, text=label, bg=SURFACE, fg=TEXT_DIM,
                     font=FONT_SM).pack(anchor="w", padx=16, pady=(6, 1))
            e = tk.Entry(left, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                         font=FONT_BODY, relief="flat", bd=6)
            e.insert(0, placeholder)
            e.bind("<FocusIn>",
                   lambda evt, ph=placeholder: (
                       evt.widget.delete(0, "end")
                       if evt.widget.get() == ph else None))
            e.pack(fill="x", padx=16, ipady=5)
            self._entries[key] = e

        # Time quantum
        tk.Label(left, text="Time Quantum (RR)", bg=SURFACE, fg=TEXT_DIM,
                 font=FONT_SM).pack(anchor="w", padx=16, pady=(6, 1))
        self._quantum_var = tk.StringVar(value="2")
        tk.Entry(left, textvariable=self._quantum_var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=TEXT, font=FONT_BODY, relief="flat", bd=6
                 ).pack(fill="x", padx=16, ipady=5)

        # Algorithm selector
        tk.Label(left, text="Algorithm", bg=SURFACE, fg=TEXT_DIM,
                 font=FONT_SM).pack(anchor="w", padx=16, pady=(10, 1))
        self._algo_var = tk.StringVar(value="FCFS")
        algo_cb = ttk.Combobox(left, textvariable=self._algo_var, state="readonly",
                               values=["FCFS", "SJF", "Round Robin"],
                               font=FONT_BODY)
        algo_cb.pack(fill="x", padx=16)

        # Buttons
        btn_cfg = dict(relief="flat", bd=0, padx=0, pady=0, font=FONT_BODY, cursor="hand2")
        tk.Button(left, text="➕  Add Process",
                  bg=ACCENT, fg="white", activebackground="#6D28D9",
                  command=self._add_process, **btn_cfg
                  ).pack(fill="x", padx=16, pady=(18, 4), ipady=7)

        tk.Button(left, text="▶  Run Simulation",
                  bg=GREEN, fg="white", activebackground="#1F7A6E",
                  command=self._run_simulation, **btn_cfg
                  ).pack(fill="x", padx=16, pady=4, ipady=7)

        tk.Button(left, text="⚡  Compare All",
                  bg="#E9C46A", fg="#1E1E2E", activebackground="#C5A14E",
                  command=self._run_compare, **btn_cfg
                  ).pack(fill="x", padx=16, pady=4, ipady=7)

        tk.Button(left, text="💾  Export CSV",
                  bg="#457B9D", fg="white", activebackground="#335E7A",
                  command=self._export_csv, **btn_cfg
                  ).pack(fill="x", padx=16, pady=4, ipady=7)

        tk.Button(left, text="🔄  Reset",
                  bg=RED, fg="white", activebackground="#B22D39",
                  command=self._reset, **btn_cfg
                  ).pack(fill="x", padx=16, pady=(4, 14), ipady=7)

        # ── Right panel: process queue table ──────────────────────────────────
        right = ttk.Frame(parent)
        right.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)

        tk.Label(right, text="Process Queue", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w", pady=(4, 6))

        cols = ("pid", "arrival", "burst", "priority")
        tree_frame = ttk.Frame(right)
        tree_frame.pack(fill="both", expand=True)

        self._proc_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", selectmode="browse")
        for c, w, lbl in zip(cols, [100, 120, 120, 100],
                              ["PID", "Arrival Time", "Burst Time", "Priority"]):
            self._proc_tree.heading(c, text=lbl)
            self._proc_tree.column(c, width=w, anchor="center")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self._proc_tree.yview)
        self._proc_tree.configure(yscrollcommand=vsb.set)
        self._proc_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Delete-process button
        tk.Button(right, text="🗑  Remove Selected",
                  bg=RED, fg="white", relief="flat", font=FONT_SM,
                  cursor="hand2", command=self._delete_selected
                  ).pack(anchor="e", pady=(8, 0), ipady=4, padx=2)

        # Status bar
        self._status_var = tk.StringVar(value="Ready – add processes to begin.")
        tk.Label(right, textvariable=self._status_var, bg=BG, fg=TEXT_DIM,
                 font=FONT_SM, anchor="w").pack(fill="x", pady=(6, 0))

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – Gantt Chart
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_gantt(self, parent):
        self._gantt_frame = ttk.Frame(parent)
        self._gantt_frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(self._gantt_frame, text="Run a simulation to see the Gantt chart.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Metrics Table
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_metrics(self, parent):
        self._metrics_outer = ttk.Frame(parent)
        self._metrics_outer.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(self._metrics_outer,
                 text="Run a simulation to see per-process metrics.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 – Algorithm Comparison
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_compare(self, parent):
        self._compare_outer = ttk.Frame(parent)
        self._compare_outer.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(self._compare_outer,
                 text="Click  ⚡ Compare All  to run all algorithms.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 – AI Recommendation
    # ══════════════════════════════════════════════════════════════════════════
    def _tab_ai(self, parent):
        self._ai_outer = ttk.Frame(parent)
        self._ai_outer.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(self._ai_outer,
                 text="Add processes and click  ▶ Run Simulation  to get an AI recommendation.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Input logic
    # ══════════════════════════════════════════════════════════════════════════
    def _add_process(self):
        try:
            pid     = self._entries["pid"].get().strip()
            arrival = self._entries["arrival"].get().strip()
            burst   = self._entries["burst"].get().strip()
            priority= self._entries["priority"].get().strip()

            # Placeholder text guard
            if not pid or pid == "P1":
                pid = f"P{len(self.processes)+1}"
            priority = priority if priority.isdigit() else "0"
            priority = priority.split()[0]   # strip "(optional)"

            # Duplicate PID check
            if any(p.pid == pid for p in self.processes):
                messagebox.showwarning("Duplicate PID",
                                       f"A process with ID '{pid}' already exists.")
                return

            proc = make_process(pid, int(arrival), int(burst), int(priority))
            self.processes.append(proc)

            self._proc_tree.insert("", "end", iid=pid,
                                   values=(proc.pid, proc.arrival, proc.burst, proc.priority))
            self._status_var.set(f"✔ Process {pid} added  ({len(self.processes)} total)")

            # Auto-increment PID suggestion
            self._entries["pid"].delete(0, "end")
            self._entries["pid"].insert(0, f"P{len(self.processes)+1}")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def _delete_selected(self):
        selected = self._proc_tree.selection()
        if not selected:
            return
        pid = selected[0]
        self.processes = [p for p in self.processes if p.pid != pid]
        self._proc_tree.delete(pid)
        self._status_var.set(f"🗑 Process {pid} removed.")

    # ══════════════════════════════════════════════════════════════════════════
    # Simulation
    # ══════════════════════════════════════════════════════════════════════════
    def _run_simulation(self):
        if not self.processes:
            messagebox.showwarning("No Processes", "Please add at least one process.")
            return

        algo = self._algo_var.get()
        try:
            q = int(self._quantum_var.get())
            if q <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Quantum", "Time quantum must be a positive integer.")
            return

        # Run chosen algorithm
        if algo == "FCFS":
            gantt = fcfs(self.processes)
        elif algo == "SJF":
            gantt = sjf(self.processes)
        else:
            gantt = round_robin(self.processes, q)

        metrics = compute_metrics(self.processes, gantt)
        self.last_gantt   = gantt
        self.last_metrics = metrics
        self.last_algo    = algo

        self._status_var.set(
            f"✔ {algo} complete │ Avg WT = {metrics['avg_wt']}  │ "
            f"Avg TAT = {metrics['avg_tat']}"
        )

        self._render_gantt(gantt, f"{algo} – Gantt Chart")
        self._render_metrics(metrics)
        self._render_ai()

        # Switch to Gantt tab
        self.nb.select(1)

    def _run_compare(self):
        if not self.processes:
            messagebox.showwarning("No Processes", "Please add at least one process.")
            return
        try:
            q = int(self._quantum_var.get())
        except ValueError:
            q = 2

        comparison = compare_algorithms(self.processes, q)
        self._render_comparison(comparison)
        self.nb.select(3)

    # ══════════════════════════════════════════════════════════════════════════
    # Render helpers
    # ══════════════════════════════════════════════════════════════════════════
    def _render_gantt(self, gantt, title):
        self.canvas_gantt = draw_gantt(gantt, title, self._gantt_frame)

    def _render_metrics(self, metrics):
        # Clear old content
        for w in self._metrics_outer.winfo_children():
            w.destroy()

        tk.Label(self._metrics_outer, text=f"Metrics — {self.last_algo}",
                 bg=BG, fg=TEXT, font=FONT_H2).pack(anchor="w", pady=(0, 8))

        cols = ("pid", "arrival", "burst", "ct", "tat", "wt")
        headers = ["PID", "Arrival", "Burst", "Completion", "Turnaround", "Waiting"]
        widths   = [70, 80, 80, 110, 110, 90]

        tree_frame = ttk.Frame(self._metrics_outer)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c, h, w in zip(cols, headers, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="center")

        for row in metrics["table"]:
            tree.insert("", "end", values=(
                row["pid"], row["arrival"], row["burst"],
                row["ct"], row["tat"], row["wt"]))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Summary row
        summary = tk.Frame(self._metrics_outer, bg=SURFACE, padx=20, pady=12)
        summary.pack(fill="x", pady=(12, 0))

        def _kv(label, val, color=ACCENT2):
            tk.Label(summary, text=label, bg=SURFACE,
                     fg=TEXT_DIM, font=FONT_SM).pack(side="left", padx=(0, 4))
            tk.Label(summary, text=str(val), bg=SURFACE,
                     fg=color, font=FONT_H2).pack(side="left", padx=(0, 24))

        _kv("Avg Waiting Time:", f"{metrics['avg_wt']}")
        _kv("Avg Turnaround Time:", f"{metrics['avg_tat']}")

    def _render_comparison(self, comparison: dict):
        for w in self._compare_outer.winfo_children():
            w.destroy()

        tk.Label(self._compare_outer, text="Algorithm Comparison",
                 bg=BG, fg=TEXT, font=FONT_H2).pack(anchor="w", pady=(0, 6))

        # Summary table
        cols = ("algo", "avg_wt", "avg_tat")
        headers = ["Algorithm", "Avg Waiting Time", "Avg Turnaround Time"]
        widths   = [220, 160, 180]

        tbl_frame = ttk.Frame(self._compare_outer)
        tbl_frame.pack(fill="x", pady=(0, 10))
        tree = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=4)
        for c, h, w in zip(cols, headers, widths):
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="center")
        for name, m in comparison.items():
            tree.insert("", "end", values=(name, m["avg_wt"], m["avg_tat"]))
        tree.pack(fill="x")

        # Bar charts
        chart_frame = ttk.Frame(self._compare_outer)
        chart_frame.pack(fill="both", expand=True)
        self.canvas_compare = draw_comparison_charts(comparison, chart_frame)

    def _render_ai(self):
        for w in self._ai_outer.winfo_children():
            w.destroy()

        try:
            q = int(self._quantum_var.get())
        except ValueError:
            q = 2

        rec = recommend(self.processes, q)

        # Banner
        banner = tk.Frame(self._ai_outer, bg=ACCENT, padx=20, pady=14)
        banner.pack(fill="x", pady=(0, 12))
        tk.Label(banner, text="🤖  AI Recommendation", bg=ACCENT,
                 fg="white", font=FONT_H1).pack(anchor="w")
        tk.Label(banner, text=f"Recommended:  {rec['algorithm']}",
                 bg=ACCENT, fg="#C4B5FD", font=("Segoe UI", 13, "bold")
                 ).pack(anchor="w", pady=(4, 0))

        # Reason box
        reason_box = tk.Frame(self._ai_outer, bg=SURFACE, padx=18, pady=14)
        reason_box.pack(fill="x", pady=(0, 10))
        tk.Label(reason_box, text="Why?", bg=SURFACE,
                 fg=ACCENT2, font=FONT_H2).pack(anchor="w")
        tk.Label(reason_box, text=rec["reason"], bg=SURFACE,
                 fg=TEXT, font=FONT_BODY, wraplength=700, justify="left"
                 ).pack(anchor="w", pady=(4, 0))

        # Scores
        scores_frame = tk.Frame(self._ai_outer, bg=BG)
        scores_frame.pack(fill="x", pady=(0, 10))
        tk.Label(scores_frame, text="Confidence Scores", bg=BG,
                 fg=TEXT, font=FONT_H2).pack(anchor="w", pady=(0, 6))

        max_score = max(rec["scores"].values(), default=1) or 1
        for algo, score in rec["scores"].items():
            row = tk.Frame(scores_frame, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{algo:<30}", bg=BG,
                     fg=TEXT, font=FONT_BODY, width=32, anchor="w").pack(side="left")
            bar_outer = tk.Frame(row, bg=SURFACE, height=18, width=300)
            bar_outer.pack(side="left")
            bar_outer.pack_propagate(False)
            fill_w = int(300 * score / max_score)
            color = ACCENT2 if algo == rec["algorithm"] else ACCENT
            tk.Frame(bar_outer, bg=color, height=18, width=fill_w
                     ).place(x=0, y=0)
            tk.Label(row, text=f"{score:.1f}%", bg=BG,
                     fg=TEXT_DIM, font=FONT_SM).pack(side="left", padx=8)

        # Tips
        if rec["tips"]:
            tips_box = tk.Frame(self._ai_outer, bg=SURFACE, padx=18, pady=12)
            tips_box.pack(fill="x", pady=(4, 0))
            tk.Label(tips_box, text="Additional Insights", bg=SURFACE,
                     fg=ACCENT2, font=FONT_H2).pack(anchor="w", pady=(0, 6))
            for tip in rec["tips"]:
                tk.Label(tips_box, text=f"  {tip}", bg=SURFACE,
                         fg=TEXT, font=FONT_BODY, anchor="w", justify="left",
                         wraplength=700).pack(anchor="w", pady=2)

    # ══════════════════════════════════════════════════════════════════════════
    # Export CSV
    # ══════════════════════════════════════════════════════════════════════════
    def _export_csv(self):
        if not self.last_metrics or not self.last_metrics.get("table"):
            messagebox.showinfo("Nothing to Export",
                                "Run a simulation first to generate metrics.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Metrics CSV",
        )
        if not path:
            return

        fieldnames = ["pid", "arrival", "burst", "priority", "ct", "tat", "wt"]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames,
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.last_metrics["table"])

        # Append summary
        with open(path, "a", newline="") as f:
            f.write(f"\nAverage Waiting Time,{self.last_metrics['avg_wt']}\n")
            f.write(f"Average Turnaround Time,{self.last_metrics['avg_tat']}\n")
            f.write(f"Algorithm,{self.last_algo}\n")

        messagebox.showinfo("Exported", f"Results saved to:\n{path}")

    # ══════════════════════════════════════════════════════════════════════════
    # Reset
    # ══════════════════════════════════════════════════════════════════════════
    def _reset(self):
        if self.processes and not messagebox.askyesno(
                "Reset", "Clear all processes and results?"):
            return

        self.processes    = []
        self.last_gantt   = []
        self.last_metrics = {}
        self.last_algo    = ""

        self._proc_tree.delete(*self._proc_tree.get_children())
        self._status_var.set("Ready – add processes to begin.")

        for w in self._gantt_frame.winfo_children():
            w.destroy()
        tk.Label(self._gantt_frame,
                 text="Run a simulation to see the Gantt chart.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

        for w in self._metrics_outer.winfo_children():
            w.destroy()
        tk.Label(self._metrics_outer,
                 text="Run a simulation to see per-process metrics.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

        for w in self._compare_outer.winfo_children():
            w.destroy()
        tk.Label(self._compare_outer,
                 text="Click  ⚡ Compare All  to run all algorithms.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

        for w in self._ai_outer.winfo_children():
            w.destroy()
        tk.Label(self._ai_outer,
                 text="Add processes and click  ▶ Run Simulation  to get an AI recommendation.",
                 bg=BG, fg=TEXT_DIM, font=FONT_BODY).pack(expand=True)

        self._entries["pid"].delete(0, "end")
        self._entries["pid"].insert(0, "P1")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
