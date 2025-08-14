# Tipster Sim (Streamlit, Monte Carlo, BeSoccer-ready)

### What it does
- Monte-Carlo simulation for staking % and skim %.
- Recommends stake/skim combo optimised for lower-tail performance.
- Risk distribution chart.
- Optional BeSoccer fetch (multi-endpoint adapter; no hardcoded key).

### Local run
```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env && nano .env  # paste your key
streamlit run app.py
```

### Deploy (Hugging Face Spaces)
1) Push this repo to GitHub.
2) Create a new **Space** → **Streamlit** → connect the repo.
3) Settings → **Secrets** → add `BESOCCER_API_KEY=YOUR_KEY`.
4) App goes live.

### Notes
- Your key is never committed; it’s read from environment variables.
- BeSoccer endpoints sometimes vary by plan/version; this adapter tries common paths automatically.
