extends "res://scripts/sim/MatchSim.gd"
## Scratch probe (never commit): MatchSim whose centre-clearance picks can be sent back to the
## whole ground (off = true: as before change C), counting how many fall to `target`.

var off := false
var target := ""
var bounce_picks := 0
var bounce_target := 0


func _pick_presser(side: int, zone: int, at_bounce := false):
	var p = super(side, zone, at_bounce and not off)
	if at_bounce and side == 1:
		bounce_picks += 1
		if str(p["id"]) == target:
			bounce_target += 1
	return p
