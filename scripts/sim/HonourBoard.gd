class_name HonourBoard
extends RefCounted
## The club honour board (C-PC-14, P-41; director 2026-10-18, rulings 5.11
## no. 112): every player who left your club with 150 games, a best and
## fairest, a Brownlow or a flag for you. Games, goals, best and fairests,
## flags, Brownlows and All-Australian jumpers as columns, newest departure
## first, each name a link to his career facts. No retired jumper numbers (not
## an AFL convention) and no museum scene.
##
## Pure rules over what the career already records; GameState keeps the store
## and saves it. Keyed by player id, never by name, so two players with one name
## or a new guernsey never share a row (ruling 109).
##
##   store = {player id: row}
##   row   = {"id", "card" (CareerFacts.name_card, his names when he is gone),
##            "from", "to" (his years with you), "games", "goals" (-1: not on
##            record, shown as a dash and never guessed), "bf", "flags",
##            "brownlow", "aa" ([years]), "left" (the season he left after, 0
##            while he is still on your list), "how" ("retired", "delisted",
##            "moved", "" while he is here or when not on record), "to_club"
##            (where he went when he moved), "facts" (what the club remembers
##            about him, Remembered.sheet_lines, kept from his last day with
##            you)}
##
## Look-up only: nothing here touches a match or a player.

const GAMES := 150
## How many remembered lines a row keeps.
const FACTS_KEPT := 6


## Does this row earn a place: 150 games, a best and fairest, a Brownlow or a
## flag for your club.
static func qualifies(row: Dictionary) -> bool:
	return int(row.get("games", 0)) >= GAMES or not (row.get("bf", []) as Array).is_empty() \
			or not (row.get("brownlow", []) as Array).is_empty() or not (row.get("flags", []) as Array).is_empty()


## His Brownlow and All-Australian years while he was with your club, from the
## honour roll (only seasons you coached, only for your club).
static func roll_years(honour_roll: Array, my_club: String, id: String) -> Dictionary:
	var out := {"brownlow": [], "aa": []}
	for e in honour_roll:
		if not (e is Dictionary) or str(e.get("my_club", "")) != my_club:
			continue
		var year := int(e.get("year", 0))
		var b: Array = e.get("brownlow", [])
		if not b.is_empty() and str((b[0] as Dictionary).get("id", "")) == id \
				and str((b[0] as Dictionary).get("club", my_club)) == my_club:
			(out["brownlow"] as Array).append(year)
		if (e.get("my_aa", []) as Array).has(id):
			(out["aa"] as Array).append(year)
	return out


## Build or refresh his row from what the career holds (GameState.with_us):
## written only when he qualifies or already has a row. Safe to call any number
## of times (a reload, both call sites): every figure is read afresh, never
## added to. A player on your list again has his departure cleared.
static func upsert(gs: Object, p: Dictionary) -> Dictionary:
	var store: Dictionary = gs.get("honour_board")
	var id := str(p.get("id", ""))
	var my_club := str(gs.get("my_club"))
	if id == "" or my_club == "":
		return {}
	var w: Dictionary = gs.call("with_us", p)
	var tally: Dictionary = gs.call("club_tally", p, my_club)
	var ry := roll_years(gs.get("honour_roll"), my_club, id)
	var spells: Array = tally.get("spells", [])
	# Only a player who was with you in this career: a spell that ended before
	# the game began is the club's history, not yours (ruling 118).
	var in_career := false
	for sp in spells:
		if int(sp[1]) > Career.BEFORE_GAME:
			in_career = true
	if not in_career and not store.has(id):
		return {}
	var row: Dictionary = (store.get(id, {}) as Dictionary).duplicate(true)
	var card := CareerFacts.name_card(p)
	card["age"] = float(p.get("age", 0.0))
	row["id"] = id
	row["card"] = card
	row["from"] = int(spells[0][0]) if not spells.is_empty() else int(row.get("from", 0))
	row["to"] = int(spells[-1][1]) if not spells.is_empty() else int(row.get("to", 0))
	row["games"] = int(w.get("games", 0))
	row["goals"] = int(w.get("goals", 0))
	row["bf"] = (w.get("bf", []) as Array).duplicate()
	row["flags"] = (w.get("flags", []) as Array).duplicate()
	row["brownlow"] = ry["brownlow"]
	row["aa"] = ry["aa"]
	var facts: Array = Remembered.sheet_lines(p, gs.get("career_facts"), my_club, w,
			gs.LEARN_JOBS, FACTS_KEPT)
	if not facts.is_empty() or not row.has("facts"):
		row["facts"] = facts
	# On your list now (a released player keeps your club code while he is a
	# free agent, so the list decides, not the code).
	var here := false
	for q in gs.get("my_list"):
		if str(q.get("id", "")) == id:
			here = true
			break
	if here:
		row["left"] = 0
		row["how"] = ""
		row["to_club"] = ""
	else:
		row["left"] = int(row.get("left", 0))
		row["how"] = str(row.get("how", ""))
		row["to_club"] = str(row.get("to_club", ""))
	if not store.has(id) and not qualifies(row):
		return {}
	store[id] = row
	return row


## He has left: refresh his row while he is still in hand, then stamp the
## season and how ("retired", "delisted", "moved"). A row already stamped keeps
## its year; a fuller "how" replaces an unknown one.
static func leave(gs: Object, p: Dictionary, how: String, to_club := "") -> void:
	var store: Dictionary = gs.get("honour_board")
	var id := str(p.get("id", ""))
	if id == "":
		return
	var before: Dictionary = (store.get(id, {}) as Dictionary).duplicate()
	upsert(gs, p)
	if not store.has(id):
		return
	var row: Dictionary = store[id]
	row["left"] = int(before.get("left", 0)) if int(before.get("left", 0)) > 0 else int(gs.get("season_year"))
	row["how"] = str(before.get("how", ""))
	row["to_club"] = str(before.get("to_club", ""))
	if str(row.get("how", "")) == "" or how == "retired":
		row["how"] = how
		row["to_club"] = to_club


## Stamp every row whose player is no longer on your list (a trade, a delisting,
## free agency, retirement), wherever he went. Rows on the list are left alone.
static func sweep(gs: Object) -> void:
	var store: Dictionary = gs.get("honour_board")
	if store.is_empty():
		return
	var mine := {}
	for p in gs.get("my_list"):
		mine[str(p.get("id", ""))] = true
	var where := {}
	var season = gs.get("season")
	if season != null:
		for code in season.lists:
			for p in season.lists[code]:
				where[str(p.get("id", ""))] = str(code)
	var fa := {}
	for p in gs.get("free_agents"):
		fa[str(p.get("id", ""))] = true
	var gone: Dictionary = gs.get("departed_names")
	for id in store:
		var row: Dictionary = store[id]
		if mine.has(id):
			# Back on your list (a release undone, a player who came home).
			row["left"] = 0
			row["how"] = ""
			row["to_club"] = ""
			continue
		if int(row.get("left", 0)) != 0:
			continue
		row["left"] = int(gs.get("season_year"))
		if where.has(id) and str(where[id]) != str(gs.get("my_club")):
			row["how"] = "moved"
			row["to_club"] = str(where[id])
		elif fa.has(id):
			row["how"] = "delisted"
		elif gone.has(id):
			row["how"] = "retired"


## The board: players who have left, newest departure first, then most games.
static func rows(store: Dictionary) -> Array:
	var out := []
	for id in store:
		var row: Dictionary = store[id]
		if int(row.get("left", 0)) > 0 and qualifies(row):
			out.append(row)
	out.sort_custom(func(a, b):
		if int(a["left"]) != int(b["left"]):
			return int(a["left"]) > int(b["left"])
		if int(a.get("games", 0)) != int(b.get("games", 0)):
			return int(a.get("games", 0)) > int(b.get("games", 0))
		return str(a["id"]) < str(b["id"]))
	return out


## An older save had no board: build it from what is on record and nothing
## more. Your list through with_us(); then every best and fairest and Brownlow
## winner at your club the honour roll names who has gone. One still in the game
## (at another club) has his full record; one who has left the game is named
## from departed_names, his games and goals a dash.
static func backfill(gs: Object, find: Callable) -> void:
	var store: Dictionary = gs.get("honour_board")
	var my_club := str(gs.get("my_club"))
	if my_club == "":
		return
	for p in gs.get("my_list"):
		upsert(gs, p)
	var gone: Dictionary = gs.get("departed_names")
	var winners := {}
	for e in gs.get("honour_roll"):
		if not (e is Dictionary) or str(e.get("my_club", "")) != my_club:
			continue
		var year := int(e.get("year", 0))
		for key in ["my_bf", "brownlow"]:
			var w: Array = e.get(key, [])
			if w.is_empty() or not (w[0] is Dictionary):
				continue
			var d: Dictionary = w[0]
			if key == "brownlow" and str(d.get("club", "")) != my_club:
				continue
			var id := str(d.get("id", ""))
			if id == "" or store.has(id):
				continue
			if not winners.has(id):
				winners[id] = {"name": str(d.get("name", "")), "bf": [], "brownlow": [], "last": 0}
			(winners[id][("bf" if key == "my_bf" else "brownlow")] as Array).append(year)
			winners[id]["last"] = maxi(int(winners[id]["last"]), year)
	for id in winners:
		var p: Dictionary = find.call(id)
		if not p.is_empty():
			upsert(gs, p)
			if store.has(id) and str(p.get("club", "")) != my_club and int(store[id].get("left", 0)) == 0:
				store[id]["left"] = int(store[id].get("to", 0))
				store[id]["how"] = "moved"
				store[id]["to_club"] = str(p.get("club", ""))
			continue
		var w: Dictionary = winners[id]
		var card: Dictionary = (gone.get(id, {}) as Dictionary).duplicate()
		if card.is_empty():
			card = {"generic_name": str(w["name"])}
		var ry := roll_years(gs.get("honour_roll"), my_club, id)
		store[id] = {"id": id, "card": card, "from": 0, "to": int(card.get("year", w["last"])),
				"games": -1, "goals": -1, "bf": w["bf"], "flags": [], "brownlow": ry["brownlow"],
				"aa": ry["aa"], "left": int(card.get("year", w["last"])), "how": "retired" if gone.has(id) else "",
				"to_club": "", "facts": []}
