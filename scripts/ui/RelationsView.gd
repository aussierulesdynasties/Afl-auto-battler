class_name RelationsView
extends RefCounted
## What the profile and Team selection read about a player's relationships
## (relationship overhaul, Phase 1 UI): his opinion of you and what it is made
## of, his temperament, his bonds and rivalries, your promises to him, and what
## leaving him out this week would cost. Read-only: nothing here changes a save.
##
## The systems behind it (Opinion, Temperament, Bonds, Promises) arrive in
## their own changes, so each is looked up by path or by method and a missing
## one reads as nothing to show. Without Opinion.gd the opinion falls back to
## Trust, the model it grew out of.

const OPINION_PATH := "res://scripts/sim/Opinion.gd"
const TEMPERAMENT_PATH := "res://scripts/sim/Temperament.gd"
const PROMISES_PATH := "res://scripts/sim/Promises.gd"
## A player rated this or more is "one of our best" when left out (the line
## GameState uses for the morale sting and the Opinion mark).
const STAR_OVR := 78

static var _scripts := {}


static func _script(path: String) -> Script:
	if not _scripts.has(path):
		_scripts[path] = load(path) if ResourceLoader.exists(path) else null
	return _scripts[path]


## The model his opinion is kept in: Opinion once it exists, else Trust.
static func _model() -> Script:
	var s := _script(OPINION_PATH)
	return s if s != null else Trust


static func _has(s: Script, method: String) -> bool:
	if s == null:
		return false
	for m in s.get_script_method_list():
		if str(m.get("name", "")) == method:
			return true
	return false


## His opinion of you: {"shown": 0..100, "marks": [{"text", "points", "weeks"}]
## (what fades, biggest first; weeks -1 when it stays), "reasons": [String]
## (what he remembers, newest first)}.
static func opinion(rel: Dictionary, id: String) -> Dictionary:
	var m := _model()
	var key: String = m.call("player_key", id)
	var out := {"shown": int(m.call("opinion", int(m.call("value", rel, key)))), "marks": [], "reasons": []}
	if _has(m, "breakdown"):
		for b in (m.call("breakdown", rel, key) as Array):
			out["marks"].append({"text": str(m.call("mark_text", b)), "points": int(b.get("points", 0)),
					"weeks": int(b.get("weeks", -1))})
	for r in (m.call("reasons", rel, key) as Array):
		out["reasons"].append(str(m.call("reason_text", r)))
	return out


## His temperament: [{"key", "label", "text", "reactions": [String]}], one or
## two of them, or [] before temperaments exist.
static func temperaments(p: Dictionary) -> Array:
	var s := _script(TEMPERAMENT_PATH)
	if s == null:
		return []
	var react := {}
	if _has(s, "reactions"):
		for r in (s.call("reactions", p) as Array):
			var k := str(r.get("key", ""))
			if not react.has(k):
				react[k] = []
			if str(r.get("text", "")) != "":
				react[k].append(str(r["text"]))
	var out := []
	for k in (s.call("of", p) as Array):
		out.append({"key": str(k), "label": str(s.call("label", str(k))), "text": str(s.call("describe", str(k))),
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
	var s := _script(PROMISES_PATH)
	if s == null:
		return []
	var out := []
	for pr in (s.call("of", gs, id) as Array):
		if str(pr.get("text", "")) != "":
			out.append(str(pr["text"]))
	return out


## Your standing as senior coach: {"respect", "authority"} out of 100, or {}
## before it is kept.
static func standing(gs: Object) -> Dictionary:
	var s := _script(PROMISES_PATH)
	if s == null or not _has(s, "standing"):
		return {}
	var st: Dictionary = s.call("standing", gs)
	return {"respect": int(st.get("respect", 50)), "authority": int(st.get("authority", 50))}


## What leaving a fit player out this week would cost, without doing it:
## {"opinion": his change from being left out, "promise": his change from a
## broken promise, "broken": [promise texts], "fallout": [{"id", "name",
## "opinion", "why"}], "respect", "authority" (the moves), "standing" (now)}.
static func drop_preview(gs: Object, p: Dictionary, rel: Dictionary, final := false) -> Dictionary:
	var id := str(p.get("id", ""))
	var out := {"opinion": 0, "promise": 0, "broken": [], "fallout": [], "respect": 0, "authority": 0,
			"standing": standing(gs)}
	var m := _model()
	if _has(m, "preview") and _has(m, "drop_mark"):
		var scale := 1.0
		var t := _script(TEMPERAMENT_PATH)
		if t != null and _has(t, "scale"):
			scale = float(t.call("scale", p, "dropped"))
		var mark: String = m.call("drop_mark", int(Rating.ovr(p, 0)), final, STAR_OVR)
		out["opinion"] = int(m.call("preview", rel, m.call("player_key", id), mark, scale))
	var s := _script(PROMISES_PATH)
	if s != null and _has(s, "preview_drop"):
		var pd: Dictionary = s.call("preview_drop", gs, id)
		out["promise"] = int(pd.get("opinion", 0))
		out["broken"] = (pd.get("broken", []) as Array).duplicate()
		out["respect"] = int(pd.get("respect", 0))
		out["authority"] = int(pd.get("authority", 0))
	if gs != null and gs.has_method("bond_fallout"):
		# Each one named as what he is to the man left out ("his brother").
		var what := {}
		for b in bonds(gs, id):
			what[str(b["id"])] = str(b["what"]) if str(b["what"]) != "" else str(b["label"]).to_lower()
		for f in (gs.call("bond_fallout", id, "drop") as Array):
			var op = GameDB.player_by_id(str(f.get("id", "")))
			if op == null or int(f.get("opinion", 0)) == 0:
				continue
			out["fallout"].append({"id": str(f["id"]), "name": GameDB.player_display_name(op), "what": str(what.get(str(f["id"]), "")),
					"opinion": int(f["opinion"]), "why": str(f.get("why", ""))})
	return out

