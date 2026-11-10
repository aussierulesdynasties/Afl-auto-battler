class_name ScoutingList
extends RefCounted
## The scouting list (row 130, director 2026-11-10): a shortlist of the coming
## National Draft class the coach keeps all season, reached from My list. Every
## week a player is on it, his club's scouts watch him (p["watch"][club] += 1),
## and their read of him narrows (DraftScouting.focus_mult), so the draft
## board, the fit marks and the list all read him the same way. It changes what
## a club knows, never the match sim.
##
## Every club keeps one (director 2026-11-09: every club gets every buff): a
## rival's scouts watch the LIMIT prospects its recruiters rate highest.
## gs.scouting_list: [{"id", "year", "round", "first": {"overall", "potential"}}].

## How many prospects a list holds (agent's number, the director's to change).
const LIMIT := 8


## The class a list draws from: the coming National Draft's, not yet drafted.
static func pool(gs) -> Array:
	return gs.preseason_prospects()


## The coach's list as it stands: entries whose prospect is still in the class,
## each with its prospect ({"entry", "p"}), in the order they were added.
static func rows(gs) -> Array:
	var by_id := {}
	for p in pool(gs):
		by_id[str(p.get("id", ""))] = p
	var out := []
	for e in gs.scouting_list:
		if e is Dictionary and by_id.has(str(e.get("id", ""))):
			out.append({"entry": e, "p": by_id[str(e["id"])]})
	return out


static func has(gs, id: String) -> bool:
	for r in rows(gs):
		if str(r["entry"]["id"]) == id:
			return true
	return false


static func full(gs) -> bool:
	return rows(gs).size() >= LIMIT


## Put a prospect on the list, noting his read as it stands. False when he is
## not in the class, already on it, or the list is full.
static func add(gs, id: String) -> bool:
	if has(gs, id) or full(gs):
		return false
	var p := {}
	for q in pool(gs):
		if str(q.get("id", "")) == id:
			p = q
	if p.is_empty():
		return false
	_prune(gs)
	var read: Dictionary = gs.prospect_reads([p]).get(id, {})
	gs.scouting_list.append({"id": id, "year": int(gs.season_year), "round": _round(gs),
			"first": {"overall": read.get("overall", [0, 0]), "potential": read.get("potential", [0, 0])}})
	gs.mark_dirty()
	return true


static func remove(gs, id: String) -> bool:
	var before: int = gs.scouting_list.size()
	gs.scouting_list = gs.scouting_list.filter(func(e): return not (e is Dictionary) or str(e.get("id", "")) != id)
	if gs.scouting_list.size() == before:
		return false
	gs.mark_dirty()
	return true


## A week played: each club's scouts watch the players on its list.
static func week(gs) -> void:
	var class_now := pool(gs)
	if class_now.is_empty():
		return
	_prune(gs)
	var watched := {}   # club -> {id: true}
	if str(gs.my_club) != "":
		var mine := {}
		for e in gs.scouting_list:
			mine[str(e.get("id", ""))] = true
		watched[str(gs.my_club)] = mine
	if gs.season != null:
		var seed: int = gs.prospect_read_seed()
		for code in gs.season.lists:
			if str(code) != str(gs.my_club):
				watched[str(code)] = _rival_picks(class_now, str(code), seed)
	for p in class_now:
		var id := str(p.get("id", ""))
		for club in watched:
			if (watched[club] as Dictionary).has(id):
				if not (p.get("watch") is Dictionary):
					p["watch"] = {}
				p["watch"][club] = int(p["watch"].get(club, 0)) + 1


## The LIMIT prospects a rival's recruiters rate highest, by its own read
## (Standard recruiting, as on draft night): {id: true}.
static func _rival_picks(class_now: Array, club: String, seed: int) -> Dictionary:
	var order := []
	for p in class_now:
		order.append([DraftScouting.scouted_worth(p, club, seed, Draft.AI_POT_WEIGHT_INTAKE), str(p.get("id", ""))])
	order.sort_custom(func(a, b):
		if not is_equal_approx(float(a[0]), float(b[0])):
			return float(a[0]) > float(b[0])
		return str(a[1]) < str(b[1]))
	var out := {}
	for row in order.slice(0, LIMIT):
		out[str(row[1])] = true
	return out


## Drop entries whose prospect has left the class (drafted, or tied elsewhere).
static func _prune(gs) -> void:
	var ids := {}
	for p in pool(gs):
		ids[str(p.get("id", ""))] = true
	gs.scouting_list = gs.scouting_list.filter(func(e): return e is Dictionary and ids.has(str(e.get("id", ""))))


## Rounds played so far (Season.round_index is the next to play: 0 before Round 1).
static func _round(gs) -> int:
	return int(gs.season.round_index) if gs.season != null else 0


## How the read has changed since he was listed, in words: "" when it has not.
## "Listed after Round 3: OVR was 57-65, POT was 64-76".
static func change_text(entry: Dictionary, now: Dictionary) -> String:
	var first: Dictionary = entry.get("first", {})
	var parts := []
	for k in [["overall", "OVR"], ["potential", "POT"]]:
		var was: Array = first.get(k[0], [])
		var is_now: Array = now.get(k[0], [])
		if was.size() == 2 and is_now.size() == 2 and (int(was[0]) != int(is_now[0]) or int(was[1]) != int(is_now[1])):
			parts.append("%s was %s" % [k[1], DraftScouting.range_text(was)])
	if parts.is_empty():
		return ""
	return "%s: %s" % [listed_when(entry), ", ".join(parts)]


## "Listed after Round 3", "Listed before Round 1".
static func listed_when(entry: Dictionary) -> String:
	var r := int(entry.get("round", 0))
	return "Listed after Round %d" % r if r > 0 else "Listed before Round 1"
