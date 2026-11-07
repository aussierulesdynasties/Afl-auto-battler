class_name MatchRings
extends RefCounted
## Who gets a ring on the oval: the players of yours you have made a call on or
## promised a run. Pure rules, read from the live sim's tactics and your list;
## nothing here decides or changes anything in the match.
##
## The order is what survives the cap. The people with a story come first (a
## run you promised, Backing), then the calls: the players you play through,
## the tagger, the spare. Your own players only: a ring means one of yours
## that you have a say about, so the match-ups the sim sets up by itself, the
## calls your assistant makes for you (MatchSim.coach_call), and the man you
## tag, are not ringed.

## The most rings on the oval at once.
const MAX := 6


## Player ids, most important first, at most MAX. `side` is yours, `my_list`
## your list (for the runs).
static func ids(sim: MatchSim, side: int, my_list: Array) -> Array:
	var out := []
	for p in my_list:
		if Backing.is_active(p):
			_add(out, str(p["id"]))
	var t: Dictionary = sim.tactics[side]
	# The three play-through picks (and an older save's single call).
	for id in sim.focus_ids(side):
		_add(out, str(id))
	# The tagger is the midfielder who goes to the man you are tagging.
	if str(t.get("tag_id", "")) != "":
		var tagger = sim.tagger_of(side)
		if tagger != null:
			_add(out, str(tagger["id"]))
	if sim.coach_call(side):
		_add(out, str(sim.interceptor[side]))
	return out.slice(0, MAX)


static func _add(out: Array, id: String) -> void:
	if id != "" and not out.has(id):
		out.append(id)
