class_name RelationsView
extends RefCounted
## What the profile and Team selection read about a player's relationships
## (relationship overhaul, Phase 1 UI): his opinion of you and what it is made
## of, his temperament, his bonds and rivalries, your promises to him, and what
## leaving him out this week would cost. Read-only: nothing here changes a save.
##
## It reads the live systems (Opinion, Temperament, Bonds through GameState,
## Promises) directly, so every number is the one the game will apply: a
## drop's mark sized by his temperament, each mate's move sized by the tie and
## by that man's own temperament (GameState.bond_fallout_moves).

## A player rated this or more is "one of our best" when left out (the line
## GameState uses for the morale sting and the Opinion mark).
const STAR_OVR := 78


## His opinion of you: {"shown": 0..100, "marks": [{"text", "points", "weeks"}]
## (what fades, biggest first; weeks -1 when it stays), "reasons": [String]
## (what he remembers, newest first)}.
static func opinion(rel: Dictionary, id: String) -> Dictionary:
	var key := Opinion.player_key(id)
	var out := {"shown": Opinion.opinion(Opinion.value(rel, key)), "marks": [], "reasons": []}
	for b in Opinion.breakdown(rel, key):
		out["marks"].append({"text": Opinion.mark_text(b), "points": int(b.get("points", 0)),
				"weeks": int(b.get("weeks", -1))})
	for r in Opinion.reasons(rel, key):
		out["reasons"].append(Opinion.reason_text(r))
	return out


## His temperament: [{"key", "label", "text", "reactions": [String]}], one or
## two of them, or [] before temperaments exist.
static func temperaments(p: Dictionary) -> Array:
	var react := {}
	for r in Temperament.reactions(p):
		var k := str(r.get("key", ""))
		if not react.has(k):
			react[k] = []
		if str(r.get("text", "")) != "":
			react[k].append(str(r["text"]))
	var out := []
	for k in Temperament.of(p):
		out.append({"key": str(k), "label": Temperament.label(str(k)), "text": Temperament.describe(str(k)),
				"reactions": react.get(str(k), [])})
	return out


## His bonds, strongest first: [{"id", "kind", "label", "name", "club"}].
static func bonds(gs: Object, id: String) -> Array:
	if gs == null or not gs.has_method("bond_ties"):
		return []
	var out := []
	for t in (gs.call("bond_ties", id) as Array):
		var other := str(t.get("id", ""))
		var op = GameDB.player_by_id(other)
		if op == null:
			continue
		out.append({"id": other, "kind": str(t.get("kind", "")), "label": str(t.get("label", "")),
				"what": str(t.get("what", "")),
				"name": GameDB.player_display_name(op), "club": str((op as Dictionary).get("club", ""))})
	return out


## Your word to him, in football words: [String].
static func promises(gs: Object, id: String) -> Array:
	if gs == null:
		return []
	var out := []
	for pr in Promises.of(gs, id):
		if str(pr.get("text", "")) != "":
			out.append(str(pr["text"]))
	return out


## The group of unhappy players he stands with at your club, in words, or ""
## (Factions.gd): who they are, how many, who leads them and what they want.
static func faction(gs: Object, id: String) -> String:
	if gs == null or not ("factions" in gs):
		return ""
	return Factions.profile_line(gs, str(gs.get("my_club")), id, func(pid: String) -> String:
		var q = GameDB.player_by_id(pid)
		return GameDB.player_display_name(q) if q != null else "a teammate")


## Your standing as senior coach, live: {"respect", "authority"} out of 100,
## or {} with no game to read.
static func standing(gs: Object) -> Dictionary:
	if gs == null:
		return {}
	var st: Dictionary = Promises.standing(gs)
	return {"respect": int(st.get("respect", Promises.START)), "authority": int(st.get("authority", Promises.START))}


## What leaving a fit player out this week would cost, without doing it:
## {"opinion": his change from being left out, "promise": his change from a
## broken promise, "broken": [promise texts], "fallout": [{"id", "name",
## "opinion", "why"}], "respect", "authority" (the moves), "standing" (now)}.
## Each number is what the round will apply (GameState._opinion_after_round).
static func drop_preview(gs: Object, p: Dictionary, rel: Dictionary, final := false) -> Dictionary:
	var id := str(p.get("id", ""))
	var out := {"opinion": 0, "promise": 0, "broken": [], "fallout": [], "respect": 0, "authority": 0,
			"standing": standing(gs)}
	var mark := Opinion.drop_mark(int(Rating.ovr(p, 0)), final, STAR_OVR)
	out["opinion"] = Opinion.preview(rel, Opinion.player_key(id), mark, Temperament.scale(p, "dropped"))
	if gs == null:
		return out
	var pd: Dictionary = Promises.preview_drop(gs, id)
	out["promise"] = int(pd.get("opinion", 0))
	out["broken"] = (pd.get("broken", []) as Array).duplicate()
	out["respect"] = int(pd.get("respect", 0))
	out["authority"] = int(pd.get("authority", 0))
	if gs.has_method("bond_fallout_moves"):
		# Each one named as what he is to the man left out ("his brother").
		var what := {}
		for b in bonds(gs, id):
			what[str(b["id"])] = str(b["what"]) if str(b["what"]) != "" else str(b["label"]).to_lower()
		for f in (gs.call("bond_fallout_moves", id, "drop") as Array):
			var op = GameDB.player_by_id(str(f.get("id", "")))
			if op == null or int(f.get("opinion", 0)) == 0:
				continue
			out["fallout"].append({"id": str(f["id"]), "name": GameDB.player_display_name(op), "what": str(what.get(str(f["id"]), "")),
					"opinion": int(f["opinion"]), "why": str(f.get("why", ""))})
	return out
