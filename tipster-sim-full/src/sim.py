from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np

@dataclass
class SimParams:
    p_win: float = 0.78
    odds: float = 1.90
    matches_per_day: int = 10
    days_per_month: int = 4
    runs: int = 20000
    start_bank: float = 250.0

def run_month(params: SimParams, stake_frac: float, skim_frac: float,
              rng: np.random.Generator) -> Dict[str, float]:
    b = params.start_bank
    safe = 0.0
    max_equity = b
    min_equity = b

    for _ in range(params.days_per_month):
        for _ in range(params.matches_per_day):
            stake = b * stake_frac
            if rng.random() < params.p_win:
                b += stake * (params.odds - 1.0)
            else:
                b -= stake
            equity = b + safe
            if equity > max_equity:
                max_equity = equity
            if equity < min_equity:
                min_equity = equity
        skim_amt = b * skim_frac
        b -= skim_amt
        safe += skim_amt

    equity = b + safe
    max_dd = 0.0 if max_equity == 0 else (max_equity - min_equity) / max_equity
    return {"bank": b, "safe": safe, "equity": equity, "max_dd": max_dd}

def sweep(params: SimParams, stake_grid, skim_grid, seed: int = 42):
    rng = np.random.default_rng(seed)
    results = {}
    for s in stake_grid:
        for k in skim_grid:
            equities = []
            safes = []
            dds = []
            for _ in range(params.runs):
                out = run_month(params, s, k, rng)
                equities.append(out["equity"])
                safes.append(out["safe"])
                dds.append(out["max_dd"])
            arr_e = np.array(equities)
            arr_s = np.array(safes)
            arr_d = np.array(dds)
            results[(s, k)] = {
                "avg_equity": float(arr_e.mean()),
                "med_equity": float(np.median(arr_e)),
                "p10_equity": float(np.percentile(arr_e, 10)),
                "p90_equity": float(np.percentile(arr_e, 90)),
                "best": float(arr_e.max()),
                "worst": float(arr_e.min()),
                "avg_safe": float(arr_s.mean()),
                "prob_half_or_worse": float((arr_e <= params.start_bank * 0.5).mean()),
                "avg_dd": float(arr_d.mean()),
            }
    return results

def recommend(results: Dict, ruin_cap: float = 0.05) -> Tuple[Tuple[float, float], Dict[str, float]]:
    best_key = None
    best_score = None
    for k, v in results.items():
        if v["prob_half_or_worse"] > ruin_cap:
            continue
        score = (v["p10_equity"], v["med_equity"])
        if best_score is None or score > best_score:
            best_key = k
            best_score = score
    if best_key is None:
        best_key = max(results, key=lambda kk: results[kk]["p10_equity"])
    return best_key, results[best_key]
