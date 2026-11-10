class_name PremiershipSide
extends RefCounted
## A club across generations (TODO row T5.r158, RC-007; Director Bible 5.15
## no. 158): its last premiership side in this career set against its list
## today, in one line on the club's page. "2028 premiership players still on
## the list: Smith, Jones and Brown."
##
## Only from what was recorded: the honour roll keeps the men who played in
## each premiership side ("premier_side", from the season the key arrived; an
## older entry lacks it and is never back-filled). A club with no flag on the
## record shows nothing; nothing is guessed from list stints or real history.
## Look-up only: no rating, morale or match effect.

## Up to this many survivors are named; more are counted.
const NAMED := 4


## The club's latest premiership with its side on record, from a season
## before `year`, against `list` (the club's players now):
## {"year", "of" (the side's size), "left" ([ids] still on the list, in the
## side's order)}. {} when there is none.
static func remains(honour_roll: Array, code: String, list: Array, year: int) -> Dictionary:
	for i in range(honour_roll.size() - 1, -1, -1):
		var e: Dictionary = honour_roll[i]
		if str(e.get("premier", "")) != code or int(e.get("year", 0)) >= year:
			continue
		var side: Array = e.get("premier_side", [])
		if side.is_empty():
			return {}   # the latest flag has no side on record: say nothing
		var here := {}
		for p in list:
			here[str(p.get("id", ""))] = true
		var left := []
		for id in side:
			if here.has(str(id)):
				left.append(str(id))
		return {"year": int(e["year"]), "of": side.size(), "left": left}
	return {}


## The line's words: the lead and the survivors, names already marked up by
## `name_of` (id -> text). "" when `r` is empty.
static func line(r: Dictionary, name_of: Callable) -> Array:
	if r.is_empty():
		return []
	var y := int(r["year"])
	var left: Array = r["left"]
	if left.is_empty():
		return ["No %d premiership players left on the list" % y, ""]
	var lead := "%d premiership players still on the list" % y
	if left.size() > NAMED:
		return [lead, "%d of %d" % [left.size(), int(r["of"])]]
	var names := left.map(func(id): return str(name_of.call(str(id))))
	var said := str(names[0]) if names.size() == 1 else \
			", ".join(names.slice(0, names.size() - 1)) + " and " + str(names[-1])
	if left.size() == 1:
		lead = "%d premiership player still on the list" % y
	return [lead, said]
