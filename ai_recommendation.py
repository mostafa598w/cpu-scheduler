"""
ai_recommendation.py
--------------------
Rule-based intelligent recommender that analyses process characteristics
and suggests the most suitable scheduling algorithm.

The heuristics are inspired by classical OS theory:

  ● FCFS   – fair, simple, good when bursts are uniform and there's no
              concern about starvation.
  ● SJF    – minimises average waiting time; ideal when burst times are
              known in advance and vary significantly.
  ● Round Robin – best for interactive / time-sharing systems; particularly
              effective when many short processes compete with longer ones.

Public API
----------
recommend(processes, quantum) → dict
    Returns {"algorithm": str, "score": dict, "reason": str, "tips": list}
"""

import statistics


# ── Heuristic weight constants ─────────────────────────────────────────────────

W_BURST_VARIANCE      = 0.35   # How much burst variation matters
W_PROCESS_COUNT       = 0.25   # How many processes are there
W_ARRIVAL_SPREAD      = 0.20   # How spread-out the arrivals are
W_SHORT_BURST_RATIO   = 0.20   # Fraction of processes with short bursts


def _burst_stats(processes):
    bursts = [p.burst for p in processes]
    mean = statistics.mean(bursts)
    stdev = statistics.pstdev(bursts) if len(bursts) > 1 else 0
    cv = stdev / mean if mean > 0 else 0          # Coefficient of Variation
    return mean, stdev, cv, bursts


def _arrival_spread(processes):
    arrivals = [p.arrival for p in processes]
    return max(arrivals) - min(arrivals)


def _short_burst_ratio(bursts, mean):
    """Fraction of processes whose burst < mean."""
    return sum(1 for b in bursts if b < mean) / len(bursts) if bursts else 0


# ── Scoring ────────────────────────────────────────────────────────────────────

def _score_fcfs(processes, mean_burst, cv, spread, short_ratio, n):
    """
    FCFS scores high when:
      - low burst variance (uniform workload)
      - few processes (overhead doesn't matter)
      - early batch-style arrival
    """
    score = 0.0
    score += (1 - min(cv, 1.0)) * W_BURST_VARIANCE        # low variance → good
    score += (1 - min(n / 20, 1.0)) * W_PROCESS_COUNT     # fewer procs → good
    score += (1 - min(spread / 50, 1.0)) * W_ARRIVAL_SPREAD
    score += (1 - short_ratio) * W_SHORT_BURST_RATIO
    return round(score * 100, 1)


def _score_sjf(processes, mean_burst, cv, spread, short_burst_ratio, n):
    """
    SJF scores high when:
      - high burst variance (so shortest-first gives big savings)
      - moderate number of processes
      - many short bursts relative to the mean
    """
    score = 0.0
    score += min(cv, 1.0) * W_BURST_VARIANCE               # high variance → good
    score += min(n / 15, 1.0) * W_PROCESS_COUNT
    score += short_burst_ratio * W_SHORT_BURST_RATIO
    score += (1 - min(spread / 50, 1.0)) * W_ARRIVAL_SPREAD
    return round(score * 100, 1)


def _score_rr(processes, mean_burst, cv, spread, short_burst_ratio, n):
    """
    Round Robin scores high when:
      - many processes (time-sharing need)
      - high arrival spread (interactive arrivals)
      - mixed burst sizes
    """
    score = 0.0
    score += min(n / 20, 1.0) * W_PROCESS_COUNT
    score += min(spread / 50, 1.0) * W_ARRIVAL_SPREAD
    score += min(cv, 1.0) * W_BURST_VARIANCE               # variance helps RR
    score += short_burst_ratio * W_SHORT_BURST_RATIO
    return round(score * 100, 1)


# ── Main recommender ───────────────────────────────────────────────────────────

def recommend(processes: list, quantum: int = 2) -> dict:
    """
    Analyse the process set and return a recommendation dict.

    Parameters
    ----------
    processes : list of Process namedtuples
    quantum   : Round Robin time quantum (used only in tip text)

    Returns
    -------
    dict with keys:
      "algorithm" – recommended algorithm name (str)
      "scores"    – {algo: score} dict (higher = better fit)
      "reason"    – primary explanation (str)
      "tips"      – list of additional advice strings
    """
    if not processes:
        return {
            "algorithm": "N/A",
            "scores": {},
            "reason": "No processes provided.",
            "tips": [],
        }

    n = len(processes)
    mean_burst, stdev, cv, bursts = _burst_stats(processes)
    spread = _arrival_spread(processes)
    short_ratio = _short_burst_ratio(bursts, mean_burst)

    fcfs_score = _score_fcfs(processes, mean_burst, cv, spread, short_ratio, n)
    sjf_score  = _score_sjf(processes,  mean_burst, cv, spread, short_ratio, n)
    rr_score   = _score_rr(processes,   mean_burst, cv, spread, short_ratio, n)

    scores = {
        "FCFS":         fcfs_score,
        "SJF":          sjf_score,
        f"Round Robin (Q={quantum})": rr_score,
    }

    best_algo = max(scores, key=scores.get)
    tips = []

    # ── Build reason text ──────────────────────────────────────────────────────
    if best_algo == "FCFS":
        reason = (
            f"With {n} process(es), relatively uniform burst times "
            f"(σ={stdev:.1f}, CV={cv:.2f}), and a compact arrival window, "
            "FCFS delivers fair, predictable scheduling with minimal overhead."
        )
        if cv > 0.5:
            tips.append("⚠ Burst variance is moderate – consider SJF to reduce average waiting time.")
        if n > 10:
            tips.append("⚠ Large process count can cause convoy effect with FCFS.")

    elif best_algo == "SJF":
        reason = (
            f"Burst times vary significantly (σ={stdev:.1f}, CV={cv:.2f}) "
            f"with {int(short_ratio*100)}% of processes below the mean burst "
            f"({mean_burst:.1f} units). SJF minimises average waiting time by "
            "always running the shortest ready job first."
        )
        tips.append("ℹ SJF is non-preemptive here – long processes may starve if short jobs keep arriving.")
        if n > 8:
            tips.append("💡 With many mixed-length jobs, Round Robin could improve responsiveness.")

    else:  # Round Robin
        reason = (
            f"The workload has {n} processes with a wide arrival spread "
            f"({spread} time units) and mixed burst sizes. Round Robin with "
            f"quantum={quantum} ensures every process gets regular CPU time, "
            "preventing starvation and improving responsiveness."
        )
        if quantum > mean_burst:
            tips.append(f"💡 Quantum ({quantum}) exceeds mean burst ({mean_burst:.1f}) – "
                        "consider a smaller quantum for better time-sharing.")
        if quantum < 1:
            tips.append("⚠ Quantum too small – overhead from context switching will dominate.")
        tips.append("ℹ Tune the quantum closer to the mean burst time for optimal throughput.")

    # Universal tips
    if n == 1:
        tips.append("ℹ Only one process – any algorithm produces identical results.")
    if spread == 0:
        tips.append("ℹ All processes arrive simultaneously – arrival order tie-breaking applies.")

    return {
        "algorithm": best_algo,
        "scores":    scores,
        "reason":    reason,
        "tips":      tips,
    }
