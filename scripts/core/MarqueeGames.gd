class_name MarqueeGames
extends RefCounted
## Recurring AFL fixture traditions. These are presentation/scheduling facts,
## never MatchSim bonuses. Future careers preserve the tradition without
## inventing calendar dates the current season model does not track.
##
## "from": the first season the tradition was played (a Legacy season before
## it has no such game, bug bash 4 L8): ANZAC Day 1995, Queen's Birthday
## 2001 (King's Birthday from 2023), Dreamtime at the 'G 2005, Easter Monday
## 2010, ANZAC Eve 2016, King's Birthday Eve 2025. "name" is the tradition's
## key (banners.json); title() is what the season calls it.

const TRADITIONS := [
	{"home": "ESS", "away": "COL", "name": "ANZAC Day", "from": 1995},
	{"home": "RIC", "away": "MEL", "name": "ANZAC Eve", "from": 2016},
	{"home": "RIC", "away": "ESS", "name": "Dreamtime at the 'G", "from": 2005},
	{"home": "MEL", "away": "COL", "name": "King's Birthday", "from": 2001,
		"older": "Queen's Birthday", "older_to": 2022},
	{"home": "ESS", "away": "CAR", "name": "King's Birthday Eve", "from": 2025},
	{"home": "HAW", "away": "GEE", "name": "Easter Monday", "from": 2010},
]


## The pair's tradition, if any, played in season `year` (0: any season).
static func tradition(a: String, b: String, year := 0) -> Dictionary:
	for item in TRADITIONS:
		if (str(item["home"]) == a and str(item["away"]) == b) or (str(item["home"]) == b and str(item["away"]) == a):
			if year > 0 and year < int(item.get("from", 0)):
				return {}
			var out: Dictionary = item.duplicate()
			out["title"] = title_of(out, year)
			return out
	return {}


## The tradition's key (banners), or "".
static func label(a: String, b: String, year := 0) -> String:
	return str(tradition(a, b, year).get("name", ""))


## What season `year` calls the tradition: Queen's Birthday until 2022.
static func title_of(item: Dictionary, year := 0) -> String:
	if item.has("older") and year > 0 and year <= int(item.get("older_to", 0)):
		return str(item["older"])
	return str(item.get("name", ""))
