"""
scheduling_algorithms.py
------------------------
Implements CPU scheduling algorithms:
  - FCFS  (First Come First Serve)
  - SJF   (Shortest Job First – non-preemptive)
  - RR    (Round Robin with configurable quantum)

Each function returns a list of GanttEntry namedtuples that describe the
schedule timeline, plus a dict mapping pid → (start, finish) pairs so
metrics can be calculated downstream.
"""

from collections import namedtuple
from copy import deepcopy

# ── Data structures ────────────────────────────────────────────────────────────

Process = namedtuple("Process", ["pid", "arrival", "burst", "priority"])
GanttEntry = namedtuple("GanttEntry", ["pid", "start", "end"])


def make_process(pid: str, arrival: int, burst: int, priority: int = 0) -> Process:
    """Factory that validates and creates a Process namedtuple."""
    if arrival < 0:
        raise ValueError(f"Process {pid}: arrival time cannot be negative.")
    if burst <= 0:
        raise ValueError(f"Process {pid}: burst time must be > 0.")
    return Process(str(pid), int(arrival), int(burst), int(priority))


# ── FCFS ───────────────────────────────────────────────────────────────────────

def fcfs(processes: list) -> list:
    """
    First Come First Serve scheduling (non-preemptive).

    Processes are sorted by arrival time and executed in that order.
    Returns a list of GanttEntry objects.
    """
    if not processes:
        return []

    sorted_p = sorted(processes, key=lambda p: (p.arrival, p.pid))
    gantt = []
    clock = 0

    for p in sorted_p:
        start = max(clock, p.arrival)          # CPU may be idle
        end = start + p.burst
        gantt.append(GanttEntry(p.pid, start, end))
        clock = end

    return gantt


# ── SJF (non-preemptive) ───────────────────────────────────────────────────────

def sjf(processes: list) -> list:
    """
    Shortest Job First – non-preemptive.

    At each scheduling decision point the ready queue is sorted by burst time.
    Ties are broken by arrival time then pid.
    Returns a list of GanttEntry objects.
    """
    if not processes:
        return []

    remaining = list(processes)
    gantt = []
    clock = 0

    while remaining:
        # Collect processes that have arrived
        ready = [p for p in remaining if p.arrival <= clock]

        if not ready:
            # No process ready – jump clock to next arrival
            clock = min(p.arrival for p in remaining)
            continue

        # Pick shortest burst; tie-break by arrival then pid
        chosen = min(ready, key=lambda p: (p.burst, p.arrival, p.pid))
        remaining.remove(chosen)

        start = clock
        end = clock + chosen.burst
        gantt.append(GanttEntry(chosen.pid, start, end))
        clock = end

    return gantt


# ── Round Robin ────────────────────────────────────────────────────────────────

def round_robin(processes: list, quantum: int = 2) -> list:
    """
    Round Robin scheduling with a configurable time quantum.

    Returns a list of GanttEntry objects.
    """
    if not processes:
        return []

    if quantum <= 0:
        raise ValueError("Time quantum must be a positive integer.")

    # Work with mutable copies so we can track remaining burst
    queue_items = sorted(
        [{"pid": p.pid, "arrival": p.arrival, "remaining": p.burst} for p in processes],
        key=lambda x: (x["arrival"], x["pid"])
    )

    gantt = []
    clock = 0
    ready_queue = []
    arrival_pool = list(queue_items)   # processes not yet in ready queue

    # Seed with processes that arrive at time 0
    _enqueue_arrivals(ready_queue, arrival_pool, clock)

    while ready_queue or arrival_pool:
        if not ready_queue:
            # CPU idle – advance to next arrival
            clock = arrival_pool[0]["arrival"]
            _enqueue_arrivals(ready_queue, arrival_pool, clock)

        current = ready_queue.pop(0)
        run_time = min(quantum, current["remaining"])
        start = clock
        end = clock + run_time

        gantt.append(GanttEntry(current["pid"], start, end))
        clock = end
        current["remaining"] -= run_time

        # Enqueue any processes that arrived during this slice BEFORE re-queueing current
        _enqueue_arrivals(ready_queue, arrival_pool, clock)

        if current["remaining"] > 0:
            ready_queue.append(current)   # put back at tail

    return gantt


def _enqueue_arrivals(ready_queue: list, pool: list, clock: int):
    """Move all processes from pool whose arrival ≤ clock into ready_queue."""
    arrived = [p for p in pool if p["arrival"] <= clock]
    for p in arrived:
        pool.remove(p)
        ready_queue.append(p)
