class_name Almanac
extends RefCounted
## The club almanac (plan step 1c, behind the switch "club_almanac"): the
## keepsake of a coach's career, one page per season. Each entry is written
## once at the season's end from what the sim really did (GameState
## _close_season_awards), and the legends who retired are added at the
## rollover, when their retirement is final. Nothing is back-filled: a season
## played before the almanac existed shows only what the honour roll already
## kept for it (rows()), and a season with neither shows nothing.
##
## Entry keys (all saved; older entries may lack any of them):
##   year, club, ladder, of, w, l, d, finals_tag, finals_text, finals_w,
##   finals_l, premier (code), runner_up (code), flag (bool: your club won it),
##   bf, brownlow, coleman ([{id, name, club, ...}] 0 or 1 row),
##   goalkicker ({id, name, goals} or {}), records ([text]), legends
##   ([{id, name, games, goals}]),
##   story_of_the_season: "" until plan step 1a writes the season's story
##   at the wrap. Kept empty on purpose: the slot is here so 1a only fills it.

## A retiring player is a club legend at either mark (career games or goals).
const LEGEND_GAMES := 150
const LEGEND_GOALS := 300
const STORY_KEY := "story_of_the_season"
const FEATURE := "club_almanac"


static func on() -> bool:
	return Features.on(FEATURE)


## The season just finished, as the almanac keeps it. `gs` is GameState,
## called after the honour roll's entry for this season is appended.
static func season_entry(gs) -> Dictionary:
	var season = gs.season
	var my: String = gs.my_club
	var roll: Dictionary = gs.honour_roll.back() if not gs.honour_roll.is_empty() else {}
	var lr: Dictionary = gs.my_ladder_row()
	var fw := 0
	var fl := 0
	var tag := ""
	for week in season.finals.get("weeks", []):
		for res in week:
			if not gs.is_my_match(res):
				continue
			tag = str(res.get("tag", ""))
			var s: Array = res.get("score", [0, 0])
			var mine := 0 if str(res.get("home", "")) == my else 1
			if int(s[mine]) > int(s[1 - mine]):
				fw += 1
			elif int(s[mine]) < int(s[1 - mine]):
				fl += 1
	var premier := str(season.finals.get("premier", ""))
	var runner := str(season.finals.get("runner_up", ""))
	var entry := {
		"year": int(gs.season_year),
		"club": my,
		"ladder": int(gs.my_position()),
		"of": int(season.ladder.size()),
		"w": int(lr.get("w", 0)), "l": int(lr.get("l", 0)), "d": int(lr.get("d", 0)),
		"finals_tag": tag,
		"finals_text": finals_text(tag, premier == my, runner == my),
		"finals_w": fw, "finals_l": fl,
		"premier": premier,
		"runner_up": runner,
		"flag": premier != "" and premier == my,
		"bf": _named(gs, roll.get("my_bf", [])),
		"brownlow": _named(gs, roll.get("brownlow", [])),
		"coleman": _named(gs, roll.get("coleman", [])),
		"goalkicker": _goalkicker(gs, my),
		"records": _records_broken(gs),
		"legends": [],
		STORY_KEY: "",
	}
	return entry


## How the finals went for you, in words.
static func finals_text(tag: String, won_flag: bool, lost_gf: bool) -> String:
	if won_flag:
		return "Premiers"
	if lost_gf:
		return "Runners-up"
	if tag == "":
		return "Missed the finals"
	var names := {"WC": "a wildcard final", "EF": "an elimination final", "QF": "a qualifying final",
			"SF": "a semi-final", "PF": "a preliminary final", "GF": "the Grand Final"}
	return "Out in %s" % str(names.get(tag.substr(0, 2), "the finals"))


## Award rows with the player's name written in, so the page can still name
## him after he has retired and left every list.
static func _named(gs, rows) -> Array:
	var out := []
	for r in rows:
		if not (r is Dictionary):
			continue
		var row: Dictionary = (r as Dictionary).duplicate()
		row["name"] = gs.award_name(row)
		out.append(row)
	return out


## Your club's leading goalkicker for the whole season (finals included).
static func _goalkicker(gs, my: String) -> Dictionary:
	var best := {}
	for id in gs.season_tally:
		var t: Dictionary = gs.season_tally[id]
		if str(t.get("club", "")) != my or int(t.get("goals", 0)) <= 0:
			continue
		if best.is_empty() or int(t["goals"]) > int(best["goals"]):
			best = {"id": str(id), "goals": int(t["goals"])}
	if not best.is_empty():
		best["name"] = gs.award_name(best)
	return best


## The league records set this season (Awards.update_records stamps each
## with the year it was set).
static func _records_broken(gs) -> Array:
	var out := []
	var year := int(gs.season_year)
	for line in gs.history_record_lines():
		if str(line).ends_with("(%d)" % year):
			out.append(str(line))
	return out


## At the rollover: your retirees who reached a legend's mark. `retired` is
## the rollover's [{id, name, club, ...}], `listed` id -> player before he left.
static func add_legends(gs, retired: Array, listed: Dictionary) -> void:
	if gs.almanac.is_empty():
		return
	var entry: Dictionary = gs.almanac.back()
	# Only onto the page of the season just closed: with the switch turned on
	# mid-career, the last page may be an older year that these men never saw out.
	if int(entry.get("year", 0)) != int(gs.season_year):
		return
	var legends: Array = entry.get("legends", [])
	for r in retired:
		if str(r.get("club", "")) != str(entry.get("club", "")):
			continue
		var p: Dictionary = listed.get(str(r.get("id", "")), {})
		if p.is_empty():
			continue
		var c := Career.of(p)
		var games := int(c.get("games", 0))
		var goals := int(c.get("goals", 0))
		if games >= LEGEND_GAMES or goals >= LEGEND_GOALS:
			legends.append({"id": str(r["id"]), "name": GameDB.player_display_name(p),
					"games": games, "goals": goals})
	entry["legends"] = legends


## Every season the page can show, newest first: the almanac's own entries,
## and for seasons played before it existed, what the honour roll kept
## (marked "partial"). A season with no record anywhere is not shown.
static func rows(almanac: Array, honour_roll: Array) -> Array:
	var have := {}
	var out := []
	for e in almanac:
		have[int(e.get("year", 0))] = true
		out.append(e)
	for h in honour_roll:
		var y := int(h.get("year", 0))
		if have.has(y):
			continue
		var my := str(h.get("my_club", ""))
		var rec := str(h.get("my_record", "")).split("-")
		var e := {"year": y, "club": my, "ladder": int(h.get("my_position", 0)),
				"premier": str(h.get("premier", "")), "runner_up": str(h.get("runner_up", "")),
				"flag": my != "" and str(h.get("premier", "")) == my,
				"bf": h.get("my_bf", []), "brownlow": h.get("brownlow", []),
				"coleman": h.get("coleman", []), "partial": true}
		if rec.size() == 3:
			e["w"] = int(rec[0])
			e["l"] = int(rec[1])
			e["d"] = int(rec[2])
		if h.has("my_finals"):
			e["finals_tag"] = str(h["my_finals"])
			e["finals_text"] = finals_text(str(h["my_finals"]), bool(e["flag"]),
					my != "" and str(h.get("runner_up", "")) == my)
		out.append(e)
	out.sort_custom(func(a, b): return int(a.get("year", 0)) > int(b.get("year", 0)))
	return out


## The coach's own record over the seasons shown: {seasons, w, l, d,
## finals_w, finals_l, finals_years, flags}.
static func coach_record(seasons: Array) -> Dictionary:
	var t := {"seasons": 0, "w": 0, "l": 0, "d": 0, "finals_w": 0, "finals_l": 0,
			"finals_years": 0, "flags": 0}
	for e in seasons:
		t["seasons"] += 1
		t["w"] += int(e.get("w", 0))
		t["l"] += int(e.get("l", 0))
		t["d"] += int(e.get("d", 0))
		t["finals_w"] += int(e.get("finals_w", 0))
		t["finals_l"] += int(e.get("finals_l", 0))
		if str(e.get("finals_tag", "")) != "":
			t["finals_years"] += 1
		if bool(e.get("flag", false)):
			t["flags"] += 1
	return t
