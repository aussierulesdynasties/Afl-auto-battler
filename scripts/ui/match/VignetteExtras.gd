class_name VignetteExtras
extends RefCounted
## Everyone else on the ground in a match vignette: the rest of both sides standing where
## that part of the ground puts them, and the field, boundary and goal umpires. A scene's
## own figures (its tokens) are the men the moment is about; these stand round them so the
## ground is never ten men on empty grass.
##
## Looks only. It reads who MatchSim has on the ground and where a side sets up
## (MatchDirector's own tables, read and never changed), draws nothing from the match's
## random numbers (each man's small offset is a hash of his id) and changes nothing.

## The fixed supporting cast of the broadcast scenes (BroadcastVignette), in oval metres at
## the +y end: x, y, who (F: the attacking side, D: the defending side, U: an umpire),
## move, facing, mirrored: forwards and their opponents paired up round the goal square,
## leading up the ground and on the wings, a man still jogging back; the goal umpire (row 14,
## moved onto the goal line when drawn), the field umpire and a boundary umpire each side.
const BROADCAST := [
	[-5.5, 68.5, "F", "ready_turn", "back", false], [-4.0, 69.6, "D", "ready_b", "front", false],
	[7.5, 63.0, "F", "ready", "back", false], [8.8, 64.4, "D", "ready_turn", "front", true],
	[-14.0, 55.0, "F", "ready_b", "back", true], [-12.5, 56.6, "D", "ready", "front", false],
	[16.0, 48.0, "F", "ready_turn", "back", true], [17.6, 49.6, "D", "ready_b", "front", true],
	[3.0, 54.0, "D", "ready_turn", "front", false], [-22.0, 42.0, "D", "ready", "front", true],
	[25.0, 58.0, "D", "ready_turn", "front", true], [26.5, 57.0, "F", "ready", "back", false],
	[-27.0, 66.0, "F", "ready_turn", "back", false], [-9.0, 40.0, "F", "jog", "front", false],
	[0.0, 80.0, "U", "ready", "front", false], [10.0, 43.0, "U", "ready_b", "front", true],
	[-49.0, 50.0, "U", "ready", "front", true], [49.0, 50.0, "U", "ready", "front", false],
]
## The umpires have no player behind them: one fixed look.
const UMPIRE_LOOK := {"skin": 1, "hair": 1}
## How far a line drifts toward the play from its set-up spot, by role (0: stays home).
const PULL := {"MID": 0.5, "RUCK": 0.5, "DEF": 0.2, "FWD": 0.2}


## A number from 0 to 1 that is always the same for that key.
static func hashf(key: String) -> float:
	return float(absi(hash(key)) % 10007) / 10006.0


## The rest of both sides: every man on the ground whose id is not in taken, as a figure
## with his own look, standing where his line sets up (oval metres: x across, y toward the
## goal my_side kicks at) and drawn toward focus as play would draw him. bounce: the
## centre-bounce set-up (wings on the wings, six in each arc, the square left to the men
## at the bounce). Each entry: the fields a scene's own figures have, plus "extra": true and
## "oval": where he stands.
static func players(sim: MatchSim, my_side: int, taken: Array, focus: Vector2, wet: bool, bounce := false) -> Array:
	var out := []
	for side in range(2):
		var sq: Squad = sim.squads[side]
		var sgn := 1.0 if side == my_side else -1.0
		var next := {}
		var spare := 0
		for p in sq.ground:
			var id := str(p["id"])
			var role := str(p.get("role", "MID"))
			if bounce and id in taken:
				continue
			var slots: Array = MatchDirector.SLOTS.get(role, [])
			var i := int(next.get(role, 0))
			while bounce and i < slots.size() and str(slots[i][0]) in MatchDirector.SQUARE:
				i += 1
			next[role] = i + 1
			var home := Vector2.ZERO
			if i < slots.size():
				var slot := str(slots[i][0])
				home = MatchDirector.CENTRE[slot] if bounce and MatchDirector.CENTRE.has(slot) else slots[i][1]
			else:
				home = MatchDirector.EXTRA_SLOTS[spare % MatchDirector.EXTRA_SLOTS.size()]
				spare += 1
			if id in taken:
				continue
			# The attacking frame (x toward the goal he kicks at) to the oval's.
			var at := Vector2(home.y, home.x) * sgn
			if not bounce:
				at = at.lerp(focus, float(PULL.get(role, 0.2)))
			at += Vector2(hashf(id + "|x") - 0.5, hashf(id + "|y") - 0.5) * (1.5 if bounce else 4.0)
			out.append({"extra": true, "side": side, "mine": side == my_side, "slot": "X", "role": "extra",
					"id": id, "tall": MatchSim._is_ruckman(p), "look": GameDB.figure_look(p, wet),
					"height_cm": float(p.get("height_cm", 0.0)), "name": "", "num": int(p.get("num", 0)),
					"tired": false, "oval": keep_in(at)})
	return out


## The umpires for play at focus (oval metres): a field umpire near it (near: where, from
## the focus; Vector2.INF for none, when the scene has its own) and two more up and down
## the ground, a boundary umpire on each wing and a goal umpire on each goal line.
static func umpires(focus: Vector2, near := Vector2(7.0, 6.0)) -> Array:
	var spots := []
	if near != Vector2.INF:
		spots.append(["field", keep_in(focus + near)])
	spots.append(["field", keep_in(focus + Vector2(-13.0, 34.0))])
	spots.append(["field", keep_in(focus + Vector2(11.0, -36.0))])
	for wing in [-1.0, 1.0]:
		var y := clampf(focus.y + 9.0 * wing, -VignetteGround.L * 0.8, VignetteGround.L * 0.8)
		var reach := (VignetteGround.A + 0.9) * sqrt(maxf(0.0, 1.0 - pow(y / VignetteGround.L, 2.0)))
		spots.append(["boundary", Vector2(reach * wing, y)])
	for end in [-1.0, 1.0]:
		spots.append(["goal", Vector2(0.0, (VignetteGround.GOAL_Y + 0.5) * end)])
	var out := []
	for i in range(spots.size()):
		out.append({"extra": true, "ump": str(spots[i][0]), "side": StoppageVignette.UMPIRE_KIT, "mine": false,
				"slot": "X", "role": "extra", "id": "umpire%d" % i, "tall": false, "look": UMPIRE_LOOK,
				"height_cm": 0.0, "name": "", "num": 0, "tired": false, "oval": spots[i][1]})
	return out


## That spot, held a couple of metres inside the boundary line.
static func keep_in(p: Vector2) -> Vector2:
	var a := VignetteGround.A - 2.0
	var l := VignetteGround.L - 2.0
	var k := sqrt(pow(p.x / a, 2.0) + pow(p.y / l, 2.0))
	return p / k if k > 1.0 else p


## The looks of a club's own players for a broadcast scene's supporting cast: n of them
## from its list, in list order, leaving out the man the scene is about (the generated look
## when the club has no list here).
static func club_looks(code: String, n: int, wet := false, skip_id := "") -> Array:
	var out := []
	var list: Array = GameDB.club_list(code) if code != "" else []
	for p in list:
		if out.size() >= n:
			break
		if p is Dictionary and str((p as Dictionary).get("id", "")) != skip_id:
			out.append({"look": GameDB.figure_look(p, wet), "num": int((p as Dictionary).get("num", 0))})
	while out.size() < n:
		out.append({"look": Appearance.generated("extra%d" % out.size()), "num": 0})
	return out


## How far a kick drifts sideways in the wind, in metres, flight 0..1 from boot to where it
## lands: nothing at either end, so the ball still leaves the boot and lands where the
## match says; most in the middle of its flight. wind: VignetteWeather.wind (0 calm .. 1).
static func drift(flight: float, wind: float, metres := 2.4) -> float:
	return sin(PI * clampf(flight, 0.0, 1.0)) * wind * metres
