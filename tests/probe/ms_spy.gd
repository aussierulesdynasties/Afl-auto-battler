extends "res://scripts/sim/MatchSim.gd"
## Scratch probe (never commit): MatchSim that remembers every call to _centre_attendees, keyed by
## the log index the next event will take, with the side's wing count on the ground at that moment.

var spy: Array = []


func _centre_attendees(side: int) -> Array:
	var out: Array = super(side)
	var nums := []
	for p in out:
		nums.append(int(p["num"]))
	var wings := 0
	var mids := 0
	for p in (squads[side] as Squad).ground:
		if str(p["role"]) == "MID":
			mids += 1
			if Roles.on_wing(p):
				wings += 1
	spy.append({"at": events.size(), "side": side, "nums": nums, "wings": wings, "mids": mids})
	return out
