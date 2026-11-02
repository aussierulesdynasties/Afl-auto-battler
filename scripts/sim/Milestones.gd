class_name Milestones
extends RefCounted
## Milestone games (plan step 3c): real career milestones read from the sim,
## for your players and for you, the coach.
##   player  games 50/100/150/200/250/300, his debut, career goals 100/200/300
##   coach   games coached 50/100/200, your first win, your first final
##
## The record lives in GameState.milestone_log, its own small structure, so
## later story arcs and the almanac can read it without the news feed:
##   {"coach": {"games", "wins", "finals"},
##    "log": [{"year", "label", "match", "who" ("player"/"coach"), "kind"
##             ("games"/"debut"/"goals"/"coached"/"first_win"/"first_final"),
##             "value", "id", "name", "club", "text"}],
##    "seen": {key: true},          # one entry per milestone, ever
##    "last_match": match key}      # the last of your matches recorded
## Recording and showing are always on (director, 2026-11-03: milestone games
## are live, no switch): the Hub card, the news front preview, the full-time line.

const PLAYER_GAMES := [50, 100, 150, 200, 250, 300]
const PLAYER_GOALS := [100, 200, 300]
const COACH_GAMES := [50, 100, 200]
## How close a goals milestone must be to show as "within reach" this week.
const GOALS_NEAR := 3


static func shown() -> bool:
	return true


static func empty() -> Dictionary:
	return {"coach": {"games": 0, "wins": 0, "finals": 0}, "log": [], "seen": {}, "last_match": ""}


## An older save: the coach's games and wins from the seasons on record (the
## honour roll's home-and-away record) plus this season's ladder; a season
## that reached the finals counts one final. Nothing already passed is
## announced again: every milestone fires on an exact count.
static func from_history(gs) -> Dictionary:
	var out := empty()
	var c: Dictionary = out["coach"]
	for h in gs.honour_roll:
		if str(h.get("my_club", "")) == "":
			continue
		var parts := str(h.get("my_record", "")).split("-")
		if parts.size() == 3:
			c["games"] = int(c["games"]) + int(parts[0]) + int(parts[1]) + int(parts[2])
			c["wins"] = int(c["wins"]) + int(parts[0])
		if str(h.get("my_finals", "")) != "":
			c["finals"] = int(c["finals"]) + 1
	if gs.season != null and gs.my_club != "":
		var r: Dictionary = gs.my_ladder_row()
		if not r.is_empty():
			c["games"] = int(c["games"]) + int(r["w"]) + int(r["l"]) + int(r["d"])
			c["wins"] = int(c["wins"]) + int(r["w"])
		# Finals already played this season (a save made mid-finals).
		for week in gs.season.finals.get("weeks", []):
			for res in week:
				var side := _my_side(gs, res)
				if side < 0:
					continue
				c["games"] = int(c["games"]) + 1
				c["finals"] = int(c["finals"]) + 1
				if _won(res, side):
					c["wins"] = int(c["wins"]) + 1
	return out


## A loaded value, made whole (a hand-edited or partial save).
static func normalise(v, gs) -> Dictionary:
	if not (v is Dictionary) or not (v as Dictionary).has("coach"):
		return from_history(gs)
	var out := empty()
	out.merge(v, true)
	var c := {"games": 0, "wins": 0, "finals": 0}
	c.merge(out["coach"] if out["coach"] is Dictionary else {}, true)
	out["coach"] = c
	return out


static func match_key(year: int, res: Dictionary) -> String:
	return "%d|%s|%s|%s" % [year, str(res.get("label", "")), str(res.get("home", "")), str(res.get("away", ""))]


static func _my_side(gs, res: Dictionary) -> int:
	if gs.my_club == "":
		return -1
	if str(res.get("home", "")) == gs.my_club:
		return 0
	if str(res.get("away", "")) == gs.my_club:
		return 1
	return -1


static func _won(res: Dictionary, side: int) -> bool:
	var s: Array = res.get("score", [0, 0])
	return s.size() == 2 and int(s[side]) > int(s[1 - side])


## What this match makes of the record, as entries. `played` says whether the
## season's tally already holds the match (after the round) or not (a full-time
## screen ahead of it): the counts are then this match's, either way.
static func _entries(gs, res: Dictionary, played: bool, coach: Dictionary) -> Array:
	var out := []
	var side := _my_side(gs, res)
	if side < 0:
		return out
	var roster: Array = res.get("roster", [])
	var stats: Dictionary = res.get("players", {})
	if side < roster.size():
		for r in roster[side]:
			var id := str(r.get("id", ""))
			var p: Dictionary = gs._find_player(id)
			if p.is_empty() or not Career.complete(p):
				continue
			var name := str(GameDB.player_display_name(p))
			var g: int = gs.games_played(p) + (0 if played else 1)
			if g == 1:
				out.append(_e("player", "debut", 1, id, name, "%s made his debut." % name))
			elif PLAYER_GAMES.has(g):
				out.append(_e("player", "games", g, id, name, "%s played his %s game." % [name, gs.ordinal(g)]))
			var kicked := int((stats.get(id, {}) as Dictionary).get("goals", 0))
			if kicked > 0:
				var after: int = gs.career_goals_before(p, 0) + (0 if played else kicked)
				var before := after - kicked
				for mark in PLAYER_GOALS:
					if before < mark and after >= mark:
						out.append(_e("player", "goals", mark, id, name, "%s kicked his %s career goal." % [name, gs.ordinal(mark)]))
	var games := int(coach["games"]) + 1
	if COACH_GAMES.has(games):
		out.append(_e("coach", "coached", games, "", "", "Your %s game as coach." % gs.ordinal(games)))
	if _won(res, side) and int(coach["wins"]) == 0:
		out.append(_e("coach", "first_win", 1, "", "", "Your first win as coach."))
	if str(res.get("tag", "")) != "" and int(coach["finals"]) == 0:
		out.append(_e("coach", "first_final", 1, "", "", "Your first final as coach."))
	return out


static func _e(who: String, kind: String, value: int, id: String, name: String, text: String) -> Dictionary:
	return {"who": who, "kind": kind, "value": value, "id": id, "name": name, "text": text}


static func _key(e: Dictionary) -> String:
	return "%s|%s|%s|%d" % [e["who"], e["id"], e["kind"], int(e["value"])]


## After a round: your match's milestones go into the record, once each, and
## the coach's counts move on. Returns the entries added.
static func record_round(gs, results: Array) -> Array:
	var added := []
	var ml: Dictionary = gs.milestone_log
	for res in results:
		var side := _my_side(gs, res)
		if side < 0:
			continue
		var mk := match_key(gs.season_year, res)
		if str(ml.get("last_match", "")) == mk:
			continue
		var coach: Dictionary = ml["coach"]
		for e in _entries(gs, res, true, coach):
			var k := _key(e)
			if (ml["seen"] as Dictionary).has(k):
				continue
			ml["seen"][k] = true
			e.merge({"year": gs.season_year, "label": str(res.get("label", "")), "match": mk, "club": gs.my_club})
			(ml["log"] as Array).append(e)
			added.append(e)
		coach["games"] = int(coach["games"]) + 1
		if _won(res, side):
			coach["wins"] = int(coach["wins"]) + 1
		if str(res.get("tag", "")) != "":
			coach["finals"] = int(coach["finals"]) + 1
		ml["last_match"] = mk
	return added


## What falls in the coming week: [{key, who, text}], for the Hub and the news.
static func upcoming(gs) -> Array:
	var out := []
	if gs.season == null or gs.my_club == "" or gs.season.is_season_over():
		return out
	var side: Dictionary = gs.current_side()
	for k in side:
		for id in side[k]:
			var p: Dictionary = gs.list_player(str(id))
			if p.is_empty() or not Career.complete(p):
				continue
			var name := str(GameDB.player_display_name(p))
			var next: int = gs.games_played(p) + 1
			if next == 1:
				out.append({"key": "debut", "who": "player", "id": str(id), "text": "%s is set to make his debut." % name})
			elif PLAYER_GAMES.has(next):
				out.append({"key": "games", "who": "player", "id": str(id), "text": "%s plays his %s game." % [name, gs.ordinal(next)]})
			var goals: int = gs.career_goals_before(p, 0)
			for mark in PLAYER_GOALS:
				if goals < mark and mark - goals <= GOALS_NEAR:
					out.append({"key": "goals", "who": "player", "id": str(id),
							"text": "%s is %d %s from %d career goals." % [name, mark - goals, "goal" if mark - goals == 1 else "goals", mark]})
	var c: Dictionary = gs.milestone_log.get("coach", {})
	var games := int(c.get("games", 0)) + 1
	if COACH_GAMES.has(games):
		out.append({"key": "coached", "who": "coach", "id": "", "text": "Your %s game as coach." % gs.ordinal(games)})
	if gs.season.is_regular_done() and int(c.get("finals", 0)) == 0 and gs.my_finals_status() == "alive":
		out.append({"key": "first_final", "who": "coach", "id": "", "text": "Your first final as coach."})
	return out


## The full-time screen's one line for this match ("" when nothing). Reads the
## record once the round is in; before that, what the match will record.
static func summary_line(gs, res: Dictionary) -> String:
	var ml: Dictionary = gs.milestone_log
	var mk := match_key(gs.season_year, res)
	var texts := []
	if str(ml.get("last_match", "")) == mk:
		for e in ml.get("log", []):
			if str(e.get("match", "")) == mk:
				texts.append(str(e["text"]))
	else:
		for e in _entries(gs, res, false, ml.get("coach", {"games": 0, "wins": 0, "finals": 0})):
			texts.append(str(e["text"]))
	return "Milestones: " + " ".join(texts) if not texts.is_empty() else ""


## The coming week's milestones in the news, one item each (switch on only).
static func preview_news(gs) -> void:
	for u in upcoming(gs):
		gs.add_news("milestone", "This week: " + str(u["text"]))
