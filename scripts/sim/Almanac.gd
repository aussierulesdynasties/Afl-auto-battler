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
##   ([{id, name, games, goals, why}]), club_records_broken ([text]),
##   season_hero ([{id, name, count}], with the match story on),
##   story_of_the_season (3 to 5 sentences, story_parts + compose) and
##   story_parts {result, hero, match, turn, arc, legends}: "arc" stays ""
##   until plan step 1a writes a coach-arc sentence into it and recomposes.

## A retiring player is a club legend at any one of these marks (director,
## 2026-11-03): goals or games for the club, club best-and-fairests, Brownlows,
## All-Australian selections, Norm Smith medals, seasons as the club's captain.
const LEGEND_MARKS := {"club_goals": 400, "club_games": 200, "club_bf": 3, "brownlow": 1,
		"all_australian": 5, "norm_smith": 1, "captain_seasons": 8}
const LEGEND_WORDS := {"club_goals": "%d goals", "club_games": "%d games", "club_bf": "%d best and fairests",
		"brownlow": "%d Brownlow", "all_australian": "%dx All-Australian", "norm_smith": "%d Norm Smith",
		"captain_seasons": "%d seasons as captain"}
## Club records kept for every club, in the order the page shows them.
const CLUB_RECORD_NAMES := {"biggest_win": "Biggest win", "highest_score": "Highest score",
		"most_goals": "Most goals in a match", "most_disposals": "Most disposals in a match",
		"longest_win_streak": "Longest winning run"}
const STORY_KEY := "story_of_the_season"
## The story's parts, kept so a later sentence (legends, a coach arc) can be
## added and the story told again (compose).
const PARTS_KEY := "story_parts"
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
		"club_records_broken": _club_records_broken(gs, my),
	}
	var sh: Array = roll.get("season_hero", [])
	if not sh.is_empty():
		entry["season_hero"] = sh.duplicate(true)
	var digest: Dictionary = gs.match_story_digest.get(str(int(gs.season_year)), {})
	var parts := story_parts(entry, digest)
	entry[PARTS_KEY] = parts
	entry[STORY_KEY] = compose(parts)
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


## At the rollover: your retirees who reached a legend's mark (legend_marks).
## `retired` is the rollover's [{id, name, club, ...}], `listed` id -> player
## before he left. Each legend's sentence is added to the season's story.
static func add_legends(gs, retired: Array, listed: Dictionary) -> void:
	if gs.almanac.is_empty():
		return
	var entry: Dictionary = gs.almanac.back()
	# Only onto the page of the season just closed: with the switch turned on
	# mid-career, the last page may be an older year that these men never saw out.
	if int(entry.get("year", 0)) != int(gs.season_year):
		return
	var club := str(entry.get("club", ""))
	var legends: Array = entry.get("legends", [])
	for r in retired:
		if str(r.get("club", "")) != club:
			continue
		var p: Dictionary = listed.get(str(r.get("id", "")), {})
		if p.is_empty():
			continue
		var why := legend_marks(p, club)
		if why.is_empty():
			continue
		var t := club_totals(p, club)
		legends.append({"id": str(r["id"]), "name": GameDB.player_display_name(p),
				"games": int(t["games"]), "goals": int(t["goals"]), "why": why})
	entry["legends"] = legends
	if entry.has(PARTS_KEY):
		entry[PARTS_KEY]["legends"] = legends_sentence(legends)
		entry[STORY_KEY] = compose(entry[PARTS_KEY])


## A player's games and goals for one club (Career stints).
static func club_totals(p: Dictionary, club: String) -> Dictionary:
	var t := {"games": 0, "goals": 0}
	for s in Career.of(p).get("stints", []):
		if s is Array and (s as Array).size() >= 5 and str(s[0]) == club:
			t["games"] += int(s[3])
			t["goals"] += int(s[4])
	return t


## Why a player is a legend of `club` (director, 2026-11-03): any one of the
## marks in LEGEND_MARKS. [] when he reached none. Honours are counted from
## when the almanac began (count_honours); nothing is back-filled.
static func legend_marks(p: Dictionary, club: String) -> Array:
	var t := club_totals(p, club)
	var h: Dictionary = p.get("honours", {}) if p.get("honours") is Dictionary else {}
	var have := {
		"club_goals": int(t["goals"]), "club_games": int(t["games"]),
		"club_bf": int((h.get("bf", {}) as Dictionary).get(club, 0)),
		"brownlow": int(h.get("brownlow", 0)), "all_australian": int(h.get("aa", 0)),
		"norm_smith": int(h.get("norm_smith", 0)),
		"captain_seasons": int((h.get("captain", {}) as Dictionary).get(club, 0)),
	}
	var out := []
	for k in LEGEND_MARKS:
		if int(have[k]) >= int(LEGEND_MARKS[k]):
			out.append(LEGEND_WORDS[k] % int(have[k]))
	return out


## At the season's close, before the honour roll: each player's honours
## (p["honours"]: bf {club: n}, brownlow, aa, norm_smith, captain {club: n},
## through), counted once a season for every club's players.
static func count_honours(gs, players: Dictionary) -> void:
	var year := int(gs.season_year)
	var aw: Dictionary = gs.season_awards
	var hit := {}
	var brown: Dictionary = aw.get("brownlow_winner", {})
	if not brown.is_empty():
		_bump(hit, str(brown.get("id", "")), "brownlow", "")
	var ns: Dictionary = aw.get("norm_smith", {})
	if not ns.is_empty():
		_bump(hit, str(ns.get("id", "")), "norm_smith", "")
	for r in aw.get("all_australian", []):
		_bump(hit, str(r.get("id", "")), "aa", "")
	var bf: Dictionary = aw.get("best_and_fairest", {})
	for code in bf:
		var rows: Array = bf[code]
		if not rows.is_empty():
			_bump(hit, str(rows[0].get("id", "")), "bf", str(code))
	for code in gs.captaincy:
		for s in (gs.captaincy[code] as Dictionary).get("slots", []):
			if str(s.get("role", "")) == "captain":
				_bump(hit, str(s.get("id", "")), "captain", str(code))
	for id in hit:
		var p: Dictionary = players.get(id, {})
		if p.is_empty():
			continue
		if not (p.get("honours") is Dictionary):
			p["honours"] = {"bf": {}, "brownlow": 0, "aa": 0, "norm_smith": 0, "captain": {}, "through": 0}
		var h: Dictionary = p["honours"]
		if int(h.get("through", 0)) >= year:
			continue
		h["through"] = year
		for k in hit[id]:
			var v = hit[id][k]
			if v is Dictionary:
				if not (h.get(k) is Dictionary):
					h[k] = {}
				for c in v:
					h[k][c] = int(h[k].get(c, 0)) + int(v[c])
			else:
				h[k] = int(h.get(k, 0)) + int(v)


static func _bump(hit: Dictionary, id: String, key: String, club: String) -> void:
	if id == "":
		return
	if not hit.has(id):
		hit[id] = {}
	if club == "":
		hit[id][key] = int(hit[id].get(key, 0)) + 1
	else:
		if not (hit[id].get(key) is Dictionary):
			hit[id][key] = {}
		hit[id][key][club] = int(hit[id][key].get(club, 0)) + 1


## The season hero (director, 2026-11-03): your player with the most match-hero
## awards this season, from the match story digest. {id, name, count} or {}
## (none, or the match story switch off). Ties go to the BF votes.
static func season_hero(gs) -> Dictionary:
	if not MatchStory.on():
		return {}
	var d: Dictionary = gs.match_story_digest.get(str(int(gs.season_year)), {})
	if d.is_empty():
		return {}
	var votes := {}
	for id in gs.season_tally:
		votes[str(id)] = int((gs.season_tally[id] as Dictionary).get("bf", 0))
	return MatchStory.season_hero(d, votes)


# ---------------------------------------------------------------------------
# Club records: every club's, checked after every match
# ---------------------------------------------------------------------------
## After a round: each club's records (gs.club_records[code]) beaten by these
## results. A record moves only when beaten outright; each is {value, who,
## year, label}. "_streak" is the club's current winning run.
static func update_club_records(gs, results: Array) -> void:
	var year := int(gs.season_year)
	for res in results:
		var score: Array = res.get("score", [])
		if score.size() < 2:
			continue
		var codes := [str(res.get("home", "")), str(res.get("away", ""))]
		var label := str(res.get("label", res.get("tag", "")))
		if label == "" and gs.season != null:
			label = "Round %d" % int(gs.season.round_index)
		var roster: Array = res.get("roster", [[], []])
		var stats: Dictionary = res.get("players", {})
		for s in [0, 1]:
			var code: String = codes[s]
			if code == "":
				continue
			if not gs.club_records.has(code):
				gs.club_records[code] = {}
			var cr: Dictionary = gs.club_records[code]
			var where := "%s v %s" % [label, GameDB.club_name(codes[1 - s])]
			var margin := int(score[s]) - int(score[1 - s])
			_beat(cr, "highest_score", int(score[s]), "", year, where)
			if margin > 0:
				_beat(cr, "biggest_win", margin, "", year, where)
			var run := int(cr.get("_streak", 0)) + 1 if margin > 0 else 0
			cr["_streak"] = run
			_beat(cr, "longest_win_streak", run, "", year, where)
			if roster.size() > s:
				for r in roster[s]:
					var st: Dictionary = stats.get(str(r.get("id", "")), {})
					var who := GameDB.player_display_name_by_id(str(r.get("id", "")), str(r.get("name", "")))
					_beat(cr, "most_goals", int(float(st.get("goals", 0.0))), who, year, where)
					_beat(cr, "most_disposals", int(float(st.get("disposals", 0.0))), who, year, where)


static func _beat(cr: Dictionary, key: String, value: int, who: String, year: int, label: String) -> void:
	if value <= 0:
		return
	var old: Dictionary = cr.get(key, {})
	if not old.is_empty() and value <= int(old.get("value", 0)):
		return
	cr[key] = {"value": value, "who": who, "year": year, "label": label}


## One club record in words, e.g. "Most goals in a match: 9, J. Smith (Round 4 v Carlton, 2027)".
static func record_line(key: String, r: Dictionary) -> String:
	var who := str(r.get("who", ""))
	return "%s: %d%s (%s, %d)" % [str(CLUB_RECORD_NAMES.get(key, key)), int(r.get("value", 0)),
			", " + who if who != "" else "", str(r.get("label", "")), int(r.get("year", 0))]


## A club's records in CLUB_RECORD_NAMES order: [{key, value, who, year, label}].
static func club_record_rows(gs, code: String) -> Array:
	var cr: Dictionary = gs.club_records.get(code, {})
	var out := []
	for k in CLUB_RECORD_NAMES:
		if cr.has(k):
			var row: Dictionary = (cr[k] as Dictionary).duplicate()
			row["key"] = k
			out.append(row)
	return out


static func _club_records_broken(gs, code: String) -> Array:
	var out := []
	for row in club_record_rows(gs, code):
		if int(row.get("year", 0)) == int(gs.season_year):
			out.append(record_line(str(row["key"]), row))
	return out


# ---------------------------------------------------------------------------
# The story of the season
# ---------------------------------------------------------------------------
## The story's parts (each "" or whole sentences), in order: result, hero,
## match, arc (plan step 1a fills it; "" until then), legends (at the rollover).
static func story_parts(entry: Dictionary, digest: Dictionary) -> Dictionary:
	var parts := {"result": "", "hero": "", "match": "", "turn": "", "arc": "", "legends": ""}
	var place := "%s of %d" % [ordinal(int(entry.get("ladder", 0))), int(entry.get("of", 0))]
	var wld := "%d-%d-%d" % [int(entry.get("w", 0)), int(entry.get("l", 0)), int(entry.get("d", 0))]
	var ft := str(entry.get("finals_text", ""))
	var club := GameDB.club_name(str(entry.get("club", "")))
	if bool(entry.get("flag", false)):
		parts["result"] = "%s were premiers in %d, from %s on the ladder at %s." % [club, int(entry["year"]), place, wld]
	elif ft == "Runners-up":
		parts["result"] = "%s lost the %d Grand Final, from %s on the ladder at %s." % [club, int(entry["year"]), place, wld]
	elif ft == "Missed the finals" or ft == "":
		parts["result"] = "%s missed the finals in %d, %s on the ladder at %s." % [club, int(entry["year"]), place, wld]
	else:
		parts["result"] = "%s finished %s at %s in %d and went out in the finals." % [club, place, wld, int(entry["year"])]
	var sh: Array = entry.get("season_hero", [])
	if not sh.is_empty():
		var n := int(sh[0].get("count", 0))
		parts["hero"] = "%s was the match hero %s." % [str(sh[0].get("name", "")),
				"once" if n == 1 else ("twice" if n == 2 else "%d times" % n)]
	elif not (entry.get("bf", []) as Array).is_empty():
		parts["hero"] = "%s won the best and fairest." % str(entry["bf"][0].get("name", ""))
	var game: Dictionary = {}
	for k in ["best_final_win", "best_win", "close_final_loss"]:
		if not (digest.get(k, {}) as Dictionary).is_empty():
			game = digest[k]
			break
	if not game.is_empty():
		parts["match"] = "The match of the year was %s: %s." % [str(game.get("label", "")), str(game.get("headline", ""))]
		parts["turn"] = str(game.get("turning_point", ""))
	elif not (entry.get("goalkicker", {}) as Dictionary).is_empty():
		var gk: Dictionary = entry["goalkicker"]
		parts["match"] = "%s kicked %d goals to lead the club." % [str(gk.get("name", "")), int(gk.get("goals", 0))]
	return parts


## The story from its parts: 3 to 5 sentences. The match's turning point is
## told only while there is room.
static func compose(parts: Dictionary) -> String:
	var out := []
	for k in ["result", "hero", "match"]:
		if str(parts.get(k, "")) != "":
			out.append(str(parts[k]))
	var tail := []
	for k in ["arc", "legends"]:
		if str(parts.get(k, "")) != "":
			tail.append(str(parts[k]))
	if str(parts.get("turn", "")) != "" and out.size() + tail.size() < 5:
		out.append(str(parts["turn"]))
	out.append_array(tail)
	return " ".join(out.slice(0, 5))


static func legends_sentence(legends: Array) -> String:
	var bits := []
	for l in legends:
		var why: Array = l.get("why", [])
		bits.append("%s (%s)" % [str(l.get("name", "")), str(why[0]) if not why.is_empty() else "%d games" % int(l.get("games", 0))])
	if bits.is_empty():
		return ""
	if bits.size() == 1:
		return "%s retired a club legend." % bits[0]
	return "%s and %s retired as club legends." % [", ".join(bits.slice(0, bits.size() - 1)), bits[-1]]


## The first sentence of a story ("" for none).
static func first_sentence(story: String) -> String:
	var i := story.find(". ")
	return story if i < 0 else story.substr(0, i + 1)


static func ordinal(n: int) -> String:
	var suffix := "th"
	if n % 100 < 11 or n % 100 > 13:
		suffix = ["th", "st", "nd", "rd", "th", "th", "th", "th", "th", "th"][n % 10]
	return "%d%s" % [n, suffix]


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
