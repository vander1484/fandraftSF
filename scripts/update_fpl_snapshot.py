#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

FPL_ENDPOINT = "https://fantasy.premierleague.com/api/bootstrap-static/"
OUTPUT = Path("data/fpl-players.json")
POSITIONS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

def number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def main():
    request = Request(
        FPL_ENDPOINT,
        headers={
            "User-Agent": "Mozilla/5.0 GitHub Actions FPL snapshot updater",
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=30) as response:
        raw = json.loads(response.read().decode("utf-8"))

    teams = {team.get("id"): team for team in raw.get("teams", [])}
    players = []

    for el in raw.get("elements", []):
        team = teams.get(el.get("team"), {})
        position = POSITIONS.get(el.get("element_type"), "")
        if not position:
            continue

        first = (el.get("first_name") or "").strip()
        second = (el.get("second_name") or "").strip()
        full_name = " ".join(part for part in [first, second] if part).strip()
        name = (el.get("web_name") or full_name or f"Player {el.get('id')}").strip()

        code = el.get("code")
        team_code = team.get("code")
        status = el.get("status") or "a"

        news_parts = []
        if status != "a":
            news_parts.append(f"Status: {status.upper()}")
        if el.get("news"):
            news_parts.append(el.get("news"))
        if el.get("chance_of_playing_next_round") is not None:
            news_parts.append(f"Chance next round: {el.get('chance_of_playing_next_round')}%")

        badge_url = ""
        if team_code:
            badge_url = f"https://resources.premierleague.com/premierleague/badges/100/t{team_code}.png"

        photo_url = ""
        if code:
            photo_url = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"

        players.append({
            "id": f"fpl-{el.get('id')}",
            "fplId": el.get("id"),
            "code": code,
            "name": name,
            "fullName": full_name,
            "club": team.get("name") or team.get("short_name") or "Unknown club",
            "clubShort": team.get("short_name") or "",
            "teamCode": team_code,
            "position": position,
            "points": int(number(el.get("total_points"), 0)),
            "guidePrice": number(el.get("now_cost"), 0) / 10,
            "lastSeasonPrice": 0,
            "note": " | ".join(news_parts) if news_parts else f"Imported from official FPL. Selected by {number(el.get('selected_by_percent'), 0):.1f}% of teams.",
            "badgeUrl": badge_url,
            "photoUrl": photo_url,
            "status": status,
            "selectedByPercent": number(el.get("selected_by_percent"), 0),
        })

    players.sort(key=lambda p: (p["position"], p["club"], p["name"]))

    snapshot = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": FPL_ENDPOINT,
        "playerCount": len(players),
        "players": players,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(players)} players to {OUTPUT}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FPL snapshot update failed: {exc}", file=sys.stderr)
        raise
