"""
metrics.py
----------
Calculates per-process and aggregate performance metrics from a
list of GanttEntry objects produced by the scheduling algorithms.

Exported functions
------------------
compute_metrics(processes, gantt)  →  dict
    Returns a dict with keys:
      "table"   – list of per-process dicts
      "avg_wt"  – average waiting time (float)
      "avg_tat" – average turnaround time (float)

format_table(metrics_dict)  →  list[dict]
    Returns the "table" portion ready for Tkinter treeview display.
"""

from collections import defaultdict
from scheduling_algorithms import GanttEntry


# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(processes: list, gantt: list) -> dict:
    """
    Given the original process list and the Gantt chart produced by a
    scheduling algorithm, calculate:
      - Completion Time  (CT)  – when the process fully finishes
      - Turnaround Time  (TAT) – CT − arrival
      - Waiting Time     (WT)  – TAT − burst

    Parameters
    ----------
    processes : list of Process namedtuples
    gantt     : list of GanttEntry namedtuples

    Returns
    -------
    dict with keys "table", "avg_wt", "avg_tat"
    """
    if not processes or not gantt:
        return {"table": [], "avg_wt": 0.0, "avg_tat": 0.0}

    # Build a lookup: pid → Process
    proc_map = {p.pid: p for p in processes}

    # Completion time = max end time across all Gantt slices for each pid
    completion = defaultdict(int)
    for entry in gantt:
        completion[entry.pid] = max(completion[entry.pid], entry.end)

    rows = []
    for pid, ct in sorted(completion.items(), key=lambda x: x[0]):
        proc = proc_map.get(pid)
        if proc is None:
            continue
        tat = ct - proc.arrival
        wt  = tat - proc.burst
        rows.append({
            "pid":      pid,
            "arrival":  proc.arrival,
            "burst":    proc.burst,
            "priority": proc.priority,
            "ct":       ct,
            "tat":      tat,
            "wt":       wt,
        })

    n = len(rows)
    avg_wt  = sum(r["wt"]  for r in rows) / n if n else 0.0
    avg_tat = sum(r["tat"] for r in rows) / n if n else 0.0

    return {
        "table":   rows,
        "avg_wt":  round(avg_wt, 3),
        "avg_tat": round(avg_tat, 3),
    }


def format_table(metrics_dict: dict) -> list:
    """Return the table rows from a metrics dict (convenience accessor)."""
    return metrics_dict.get("table", [])


def compare_algorithms(processes: list, quantum: int = 2) -> dict:
    """
    Run all three algorithms on the same process set and return a
    combined dict of metrics keyed by algorithm name.

    Parameters
    ----------
    processes : list of Process namedtuples
    quantum   : int – time quantum for Round Robin

    Returns
    -------
    dict  {algorithm_name: metrics_dict, ...}
    """
    from scheduling_algorithms import fcfs, sjf, round_robin

    algorithms = {
        "FCFS":         lambda: fcfs(processes),
        "SJF":          lambda: sjf(processes),
        f"Round Robin (Q={quantum})": lambda: round_robin(processes, quantum),
    }

    results = {}
    for name, run in algorithms.items():
        gantt = run()
        results[name] = compute_metrics(processes, gantt)

    return results
