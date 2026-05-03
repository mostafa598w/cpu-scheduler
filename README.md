# Smart CPU Scheduling System — AI-Optimised

A complete Python desktop application for simulating and comparing CPU scheduling algorithms,
with AI-based recommendations and rich Matplotlib visualisations.

---

## Project Structure

```
cpu_scheduler/
├── main.py                  ← Entry point (run this)
├── gui.py                   ← Tkinter GUI (5-tab layout)
├── scheduling_algorithms.py ← FCFS, SJF, Round Robin
├── metrics.py               ← WT, TAT, averages, comparison runner
├── visualization.py         ← Gantt chart & bar chart (Matplotlib)
├── ai_recommendation.py     ← Heuristic AI recommender
└── README.md
```

---

## Requirements

- Python 3.8+
- Tkinter (bundled with standard Python on Windows/macOS; on Linux: `sudo apt install python3-tk`)
- Matplotlib and NumPy:

```bash
pip install matplotlib numpy
```

---

## How to Run

```bash
cd cpu_scheduler
python main.py
```

---

## Features

### GUI Tabs

| Tab | Description |
|-----|-------------|
| 🖊 Input & Run | Add/delete processes, choose algorithm, run or compare |
| 📊 Gantt Chart | Colour-coded timeline rendered with Matplotlib |
| 📋 Metrics | Per-process CT / TAT / WT table + averages |
| 🔀 Compare | Run all 3 algorithms, side-by-side bar charts |
| 🤖 AI Suggest | Heuristic recommendation with confidence scores |

### Algorithms

| Algorithm | Type | Description |
|-----------|------|-------------|
| FCFS | Non-preemptive | Processes run in order of arrival |
| SJF | Non-preemptive | Shortest ready job executes first |
| Round Robin | Preemptive | Each process gets a fixed time slice (quantum) |

### Metrics Calculated

- **Completion Time (CT)** – when the process finishes
- **Turnaround Time (TAT)** – CT − Arrival
- **Waiting Time (WT)** – TAT − Burst
- **Average WT / Average TAT** – aggregate per algorithm

### AI Recommendation

A rule-based heuristic scores each algorithm against:
- Burst time variance (coefficient of variation)
- Number of processes
- Arrival-time spread
- Ratio of short-to-long burst processes

The highest-scoring algorithm is recommended with a plain-English reason and actionable tips.

### Extra Features

- ✅ Input validation (negative times, duplicate PIDs, empty fields)
- 💾 Export metrics to CSV (`File → Export CSV`)
- 🔄 Full reset clears all state and charts
- Dark-mode UI with distinct per-process colours

---

## Sample Processes to Test

| PID | Arrival | Burst | Priority |
|-----|---------|-------|----------|
| P1  | 0       | 5     | 2        |
| P2  | 1       | 3     | 1        |
| P3  | 2       | 8     | 3        |
| P4  | 3       | 2     | 1        |
| P5  | 4       | 6     | 2        |

---

## Architecture Notes

- Each module is independently importable and testable.
- `visualization.py` uses `matplotlib.use("TkAgg")` to embed charts in Tkinter frames.
- `metrics.py` depends only on `scheduling_algorithms.py` (no GUI coupling).
- The GUI wires everything together but never implements business logic itself.
