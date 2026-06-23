import json
import os
import urllib.request
from datetime import datetime, timezone

FPL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
OUTPUT_PATH = "data/fpl-players.json"

POSITION_MAP = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


def build_photo_url(photo):
    if not photo:
        return ""
    code = str(photo).replace(".jpg", "").replace(".png", "")
    return f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{code}.png"


def main():
    print("Fetching latest FPL bootstrap data...")

    request = urllib.request.Request(
        FPL_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")

    data = json.loads(raw)

    teams_by_id = {
        team["id"]: team
        for team in data.get("teams", [])
    }

    players = []

    for element in data.get("elements", []):
        team = teams_by_id.get(element.get("team"), {})
        position = POSITION_MAP.get(element.get("element_type"), "UNK")

        first_name = element.get("first_name") or ""
        second_name = element.get("second_name") or ""
        web_name = element.get("web_name") or f"{first_name} {second_name}".strip()

        status = element.get("status") or ""
        news = element.get("news") or ""
        note_parts = []

        if status and status != "a":
            note_parts.append(f"Status: {status}")

        if news:
            note_parts.append(news)

        players.append({
            "id": f"fpl-{element.get('id')}",
            "fplId": element.get("id"),
            "name": web_name,
            "fullName": f"{first_name} {second_name}".strip(),
            "club": team.get("name", ""),
            "clubShort": team.get("short_name", ""),
            "position": position,
            "points": int(element.get("total_points") or 0),
            "guidePrice": round((element.get("now_cost") or 0) / 10, 1),
            "lastSeasonPrice": 0,
            "note": " | ".join(note_parts),
            "badgeUrl": "",
            "photoUrl": build_photo_url(element.get("photo")),
            "soldTo": None,
            "soldPrice": None,
        })

    players.sort(key=lambda player: (-player["points"], player["position"], player["name"]))

    snapshot = {
        "source": "Official FPL bootstrap-static snapshot",
        "sourceUrl": FPL_URL,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "playerCount": len(players),
        "players": players,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(snapshot, file, ensure_ascii=False, indent=2)

    print(f"Wrote {len(players)} players to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
