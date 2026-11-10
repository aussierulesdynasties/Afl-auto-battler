class_name CoachLedger
extends RefCounted
## The coach's ledger on Season stats (P-39, director "Yes" 2026-10-18): the
## players you drafted who won your best and fairest or made the All-Australian
## team, and the board's verdict on each season. Pure rules over what the
## career already records; writes nothing but the season-close snapshot
## (snapshot()), which keeps a draftee's honours on the ledger after he has
## left the game.
##
## Sources, never guessed at:
##   honour_roll   one entry a season: "my_club", "my_bf" ([{id, ...}], your
##                 club's best and fairest), "my_aa" ([id], your All-Australians)
##                 and, from this patch, "my_drafted" ({id: [year, pick, kind]},
##                 which of them you drafted, written when the season closed)
##   board.history [{year, goal, met, position, verdict}], one a season
##   the player    "drafted_club", "drafted_year", "drafted_pick", "drafted_type"
##                 (GameState._mark_drafted), for seasons closed before the
##                 snapshot existed, while he is still in the game
##
## "You drafted him": the club that drafted him is the club you coached in the
## season of that draft, in a draft held in your career; or he was in the 2026
## draft class and your opening league redraft took him. A draft in a season
## you were not at the club is never yours, and a player who has left the game
## from a season closed before the snapshot is left off rather than guessed.


## The club you coached in a season: the honour roll's entry for it, your club
## now for the season in play, "" for a season you were not coaching.
static func club_in(year: int, honour_roll: Array, my_club: String, season_year: int) -> String:
	for e in honour_roll:
		if e is Dictionary and int(e.get("year", 0)) == year:
			return str(e.get("my_club", ""))
	return my_club if year >= season_year else ""


## How you drafted him, [year, pick, kind] (pick 0 when there was none; kind
## "redraft" for the opening league redraft), or [] when he was not yours.
static func your_draft(p: Dictionary, honour_roll: Array, my_club: String, season_year: int,
		first_season: int, start_mode: String) -> Array:
	var dc := str(p.get("drafted_club", ""))
	if dc == "":
		return []
	if p.has("drafted_year"):
		var y := int(p["drafted_year"])
		# A draft is held in the year before the season its players first play: the
		# draft that opened your career (real lists, or the one you walked into after
		# years simmed ahead) is stamped the year before your first season.
		if first_season > 0 and y < first_season - 1:
			return []
		var as_of := first_season if first_season > 0 and y == first_season - 1 else y
		if club_in(as_of, honour_roll, my_club, season_year) != dc:
			return []
		return [y, int(p.get("drafted_pick", 0)), str(p.get("drafted_type", "national"))]
	# The 2026 class taken in the opening league redraft (GameState.start_season
	# marks only the club that took him).
	if start_mode == "redraft" and str(p.get("id", "")).begins_with("D2026_") and first_season > 0 \
			and club_in(first_season, honour_roll, my_club, season_year) == dc:
		return [first_season, 0, "redraft"]
	return []


## The draft in football words: "Pick 7, 2027 national draft".
static func draft_words(d: Array) -> String:
	if d.size() < 3:
		return ""
	var y := int(d[0])
	var pick := int(d[1])
	var kind := str(d[2])
	if kind == "redraft":
		return "Taken in your %d league redraft" % y
	var what: String = {"national": "national draft", "rookie": "rookie draft", "midseason": "mid-season draft",
			"FS": "draft, father-son", "NGA": "draft, Next Generation Academy"}.get(kind, "draft")
	if pick > 0:
		return "Pick %d, %d %s" % [pick, y, what]
	return "%d %s" % [y, what]


## Written once as a season closes, for its honour-roll entry: which of this
## season's best and fairest and All-Australians you drafted.
## `find` is id -> the player ({} when gone).
static func snapshot(entry: Dictionary, find: Callable, honour_roll: Array, my_club: String, season_year: int,
		first_season: int, start_mode: String) -> Dictionary:
	var out := {}
	for id in _honoured(entry):
		var p: Dictionary = find.call(id)
		if p.is_empty():
			continue
		var d := your_draft(p, honour_roll, my_club, season_year, first_season, start_mode)
		if not d.is_empty():
			out[id] = d
	return out


## Your draftees with honours, as [{id, draft: [year, pick, kind], bf: [years],
## aa: [years], club}], the latest honour first. `find` is id -> the player.
static func draftees(honour_roll: Array, find: Callable, my_club: String, season_year: int,
		first_season: int, start_mode: String) -> Array:
	var by_id := {}
	for e in honour_roll:
		if not (e is Dictionary) or str(e.get("my_club", "")) == "":
			continue
		var y := int(e.get("year", 0))
		var kept: Dictionary = e.get("my_drafted", {}) if e.get("my_drafted") is Dictionary else {}
		for id in _honoured(e):
			var d: Array = []
			if e.has("my_drafted"):
				d = (kept.get(id, []) as Array).duplicate()
			else:
				var p: Dictionary = find.call(id)
				if not p.is_empty():
					d = your_draft(p, honour_roll, my_club, season_year, first_season, start_mode)
			if d.is_empty():
				continue
			if not by_id.has(id):
				by_id[id] = {"id": id, "draft": d, "bf": [], "aa": [], "club": str(e.get("my_club", "")), "last": 0}
			var row: Dictionary = by_id[id]
			if _bf_id(e) == id:
				(row["bf"] as Array).append(y)
			if (e.get("my_aa", []) as Array).has(id):
				(row["aa"] as Array).append(y)
			row["last"] = maxi(int(row["last"]), y)
	var out := by_id.values()
	out.sort_custom(func(a, b):
		if int(a["last"]) != int(b["last"]):
			return int(a["last"]) > int(b["last"])
		return str(a["id"]) < str(b["id"]))
	return out


## The board's verdict on each season, newest first: [{year, club, goal, met,
## position, verdict}].
static func verdicts(board: Dictionary, honour_roll: Array, my_club: String, season_year: int) -> Array:
	var out := []
	for h in board.get("history", []):
		if not (h is Dictionary):
			continue
		var y := int(h.get("year", 0))
		var c := club_in(y, honour_roll, my_club, season_year)
		out.append({"year": y, "club": c if c != "" else my_club, "goal": str(h.get("goal", "")),
				"met": bool(h.get("met", false)), "position": int(h.get("position", 0)),
				"verdict": str(h.get("verdict", ""))})
	out.sort_custom(func(a, b): return int(a["year"]) > int(b["year"]))
	return out


## "Finish in the top four: finished 3rd, goal met."
static func goal_line(v: Dictionary) -> String:
	var parts := PackedStringArray()
	var pos := int(v.get("position", 0))
	if pos > 0:
		parts.append("finished %s" % Almanac.ordinal(pos))
	parts.append("goal met" if bool(v.get("met", false)) else "goal missed")
	var tail := ", ".join(parts)
	var goal := str(v.get("goal", ""))
	if goal == "":
		return tail.left(1).to_upper() + tail.substr(1) + "."
	return "%s: %s." % [goal, tail]


static func _bf_id(e: Dictionary) -> String:
	var rows = e.get("my_bf", [])
	if rows is Array and not (rows as Array).is_empty() and rows[0] is Dictionary:
		return str((rows[0] as Dictionary).get("id", ""))
	return ""


static func _honoured(e: Dictionary) -> Array:
	var ids := []
	var bf := _bf_id(e)
	if bf != "":
		ids.append(bf)
	for id in e.get("my_aa", []):
		if not ids.has(str(id)):
			ids.append(str(id))
	return ids
