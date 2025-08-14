import os
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from src.sim import SimParams, sweep, recommend, run_month
from src.plotting import plot_distribution
from src.besoccer import get_laliga_fixtures, get_standings
from src.selection import pick_matches

st.set_page_config(page_title="Tipster Strategy", layout="wide")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# Sidebar controls (used by Simulator tab)
with st.sidebar:
    st.header("Simulation Inputs")
    bankroll = st.number_input("Starting bankroll (€)", 50.0, 100000.0, 250.0, 50.0)
    accuracy = st.slider("Prediction accuracy", 0.50, 0.95, 0.78, 0.01)
    odds = st.number_input("Average odds (decimal)", 1.01, 5.0, 1.90, 0.01)
    matches_per_day = st.number_input("Matches per matchday", 1, 40, 10, 1)
    days_per_month = st.number_input("Matchdays per month", 1, 12, 4, 1)
    runs = st.number_input("Monte Carlo runs", 1000, 100000, 20000, 1000)
    seed = st.number_input("Random seed", 1, 10**6, 42, 1)

    st.markdown("---")
    st.subheader("Grid Search")
    stake_min = st.slider("Stake % min", 1, 50, 5, 1)
    stake_max = st.slider("Stake % max", stake_min, 50, 25, 1)
    stake_step = st.slider("Stake % step", 1, 10, 5, 1)
    skim_min = st.slider("Skim % min", 0, 60, 10, 1)
    skim_max = st.slider("Skim % max", skim_min, 60, 30, 1)
    skim_step = st.slider("Skim % step", 1, 10, 5, 1)

tabs = st.tabs(["Simulator", "Live Picks", "Plan & Checklist"])

# =============== Simulator TAB ===============
with tabs[0]:
    st.title("Simulator")
    st.caption("Tip: if the free hardware feels slow, start with 5,000 runs, then increase to 20,000.")

    if st.button("Run Monte Carlo"):
        params = SimParams(
            p_win=float(accuracy),
            odds=float(odds),
            matches_per_day=int(matches_per_day),
            days_per_month=int(days_per_month),
            runs=int(runs),
            start_bank=float(bankroll)
        )
        stake_grid = [x/100 for x in range(stake_min, stake_max + 1, stake_step)]
        skim_grid = [x/100 for x in range(skim_min, skim_max + 1, skim_step)]

        with st.spinner("Simulating..."):
            results = sweep(params, stake_grid=stake_grid, skim_grid=skim_grid, seed=int(seed))

        rows = []
        for (s, k), v in results.items():
            rows.append({
                "Stake %": int(round(s*100)),
                "Skim %": int(round(k*100)),
                "Median Equity €": round(v["med_equity"], 2),
                "Avg Equity €": round(v["avg_equity"], 2),
                "P10 €": round(v["p10_equity"], 2),
                "P90 €": round(v["p90_equity"], 2),
                "Best €": round(v["best"], 2),
                "Worst €": round(v["worst"], 2),
                "Avg Safe Pot €": round(v["avg_safe"], 2),
                "Prob ≤50% Start": f"{v['prob_half_or_worse']:.2%}",
                "Avg Max DD": f"{v['avg_dd']:.2%}",
            })
        df = pd.DataFrame(rows).sort_values(by=["Median Equity €"], ascending=False)
        st.subheader("Results")
        st.dataframe(df, use_container_width=True)

        key, rec = recommend(results)
        s, k = key
        st.markdown(
            f"**Recommendation:** Stake **{int(round(s*100))}%** and skim **{int(round(k*100))}%** "
            f"(P10={rec['p10_equity']:.2f}, Median={rec['med_equity']:.2f}, "
            f"Avg DD={rec['avg_dd']:.2%}, Prob≤50% start={rec['prob_half_or_worse']:.2%})."
        )

        st.subheader("Risk Profile (Total Equity Distribution)")
        rng = np.random.default_rng(int(seed))
        vals = [run_month(params, s, k, rng)["equity"] for _ in range(int(runs))]
        outfile = Path("risk_profile.png")
        plot_distribution(vals, str(outfile))
        st.image(str(outfile), caption="Monte Carlo – Monthly Total Equity Distribution", use_column_width=True)

# =============== Live Picks TAB ===============
with tabs[1]:
    st.title("Live Picks (BeSoccer)")
    st.caption("Works if your Space secret **BESOCCER_API_KEY** is set.")
    colA, colB = st.columns([1, 3])
    with colA:
        if st.button("Fetch fixtures & suggest picks"):
            try:
                fixtures = get_laliga_fixtures()
                standings = get_standings()
                picks = pick_matches(fixtures, standings, max_per_matchday=10)
                st.success(f"Fixtures fetched: {len(fixtures)} | Candidate picks: {len(picks)}")
                st.dataframe(pd.DataFrame(picks), use_container_width=True)
            except Exception as e:
                st.error(str(e))
    with colB:
        st.info("Selection rule (starter): prefer ≥6-place rank gaps; avoid tight table neighbours. Edit `src/selection.py` to customise.")

# =============== Plan & Checklist TAB ===============
with tabs[2]:
    st.title("Operating Plan & Daily Checklist")

    st.markdown("""
**Stake sizing (safe yet high-yield)**
- Fixed fraction per bet; compound intra-day.
- Optimise via the simulator: choose the % pair that maximises **P10 equity** with **≤5%** probability of halving.

**Bankroll rules**
- Start €250 (or your size).
- Skim **15–25%** of active bankroll after each matchday into a **safe pot**.
- Pause if total equity ≤70% of start for two straight matchdays; review selection.

**Match selection**
- Prioritise rank-gap mismatches (≥6 places).
- Avoid derbies and near-neighbour table clashes.
- Skip matches with adverse late team-news or sharp price drift against your side.

**Volume**
- Target **3–8** strong edges per matchday; do not force 10.

**Losing streak mitigation**
- If 4 losses in last 8 bets → halve stake next matchday.
- Keep skimming regardless, to bank confidence capital.

**Daily checklist**
1) Pull fixtures and table.
2) Apply your selection filters; keep 3–8 edges.
3) Re-check injuries/suspensions and price drift.
4) Place bets at fixed fraction.
5) Record outcomes.
6) End of matchday: skim chosen % to the safe pot.
7) Weekly: re-run simulator with latest accuracy; ensure Prob(≤50% start) ≤ 5%.
    """)

# Simple health indicator
api_present = bool(os.getenv("BESOCCER_API_KEY"))
st.sidebar.markdown("---")
st.sidebar.write(f"BeSoccer key set: **{'Yes' if api_present else 'No'}**")
