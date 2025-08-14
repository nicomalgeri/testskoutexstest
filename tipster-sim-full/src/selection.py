from typing import List, Dict, Any

def pick_matches(fixtures: List[Dict[str, Any]],
                 standings: List[Dict[str, Any]],
                 max_per_matchday: int = 10) -> List[Dict[str, Any]]:
    rank = {row["team"]: i+1 for i, row in enumerate(sorted(
        standings, key=lambda x: (-int(x.get("pts", 0)), x.get("team", ""))
    ))}
    picks = []
    for m in fixtures:
        h, a = m.get("home"), m.get("away")
        if h in rank and a in rank:
            gap = abs(rank[h] - rank[a])
            if gap >= 6:
                picks.append({**m, "note": f"rank_gap={gap}"})
    return picks[:max_per_matchday]
