import os
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("BESOCCER_API_KEY", "")
BASE_URL = "https://apiclient.besoccer.com"

def _get_try(paths: List[str], params: Dict[str, Any]) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Missing BESOCCER_API_KEY. Add it to .env (local) or host Secrets (online).")
    errors = []
    for path in paths:
        url = f"{BASE_URL}{path}"
        # Try with token and key styles
        for auth_param in ({"token": API_KEY}, {"key": API_KEY}):
            q = {**params, **auth_param, "format": "json"}
            try:
                r = requests.get(url, params=q, timeout=20)
                if r.status_code == 200:
                    return r.json()
                errors.append(f"{url} [{auth_param}] -> {r.status_code}")
            except Exception as e:
                errors.append(f"{url} err {e}")
    raise RuntimeError("BeSoccer request failed. Tried: " + " | ".join(errors))

def _first_list(d: Dict[str, Any], candidates: List[str]) -> List[Any]:
    for k in candidates:
        v = d.get(k)
        if isinstance(v, list):
            return v
    # nested
    for k in candidates:
        v = d.get(k)
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, list):
                    return vv
    return []

def get_laliga_fixtures(season: Optional[str] = None) -> List[Dict[str, Any]]:
    data = _get_try(
        paths=["/v1/matches", "/v2/matches", "/v1/fixtures", "/v2/fixtures"],
        params={
            "competition": "es1",              # LaLiga (common code; adjust if your account differs)
            "season": season or "current",
            "type": "next"                     # upcoming fixtures
        }
    )
    items = _first_list(data, ["matches", "data", "result", "response"])
    fixtures = []
    for m in items:
        home = None
        away = None
        if isinstance(m.get("localTeam"), dict):
            home = m["localTeam"].get("name")
        if isinstance(m.get("visitorTeam"), dict):
            away = m["visitorTeam"].get("name")
        fixtures.append({
            "match_id": m.get("id") or m.get("match_id") or m.get("matchId"),
            "date": m.get("date") or m.get("match_date") or m.get("time") or m.get("datetime"),
            "home": home or m.get("home") or m.get("localteam") or m.get("local_team") or m.get("homeTeam"),
            "away": away or m.get("away") or m.get("visitorteam") or m.get("visitor_team") or m.get("awayTeam"),
        })
    return [x for x in fixtures if x.get("home") and x.get("away")]

def get_standings(competition: str = "es1", season: Optional[str] = None) -> List[Dict[str, Any]]:
    data = _get_try(
        paths=["/v1/standings", "/v2/standings", "/v1/leagueTable", "/v2/leagueTable"],
        params={
            "competition": competition,
            "season": season or "current"
        }
    )
    items = _first_list(data, ["table", "data", "standings", "result", "response"])
    table = []
    for t in items:
        team = None
        if isinstance(t.get("team"), dict):
            team = t["team"].get("name")
        team = team or t.get("team") or t.get("team_name") or t.get("name")
        pts = t.get("points") or t.get("pts") or t.get("puntos") or t.get("score")
        gf = t.get("goals_for") or t.get("gf") or t.get("goalsFor")
        ga = t.get("goals_against") or t.get("ga") or t.get("goalsAgainst")
        form = t.get("form") or t.get("racha") or ""
        table.append({"team": team, "pts": pts or 0, "gf": gf or 0, "ga": ga or 0, "form": form})
    return [x for x in table if x.get("team")]
