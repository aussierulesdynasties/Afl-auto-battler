class_name DecisionVignette
extends StoppageVignette
## A staged close-up for each in-match call that was still a text card (TODO row 13):
## a star running on empty (tired), a forward getting on top (duel), a midfielder
## kicking a bag (hot), a run of goals against (momentum), a set shot at goal
## (set_shot). The late centre-bounce call has its own scene (StoppageVignette).
##
## The match cuts to a low camera on a long lens, the players the call is about move into
## place and the frame freezes; the call slides up over it (MatchScene._show_moment). Round
## them stand the rest of both sides and the umpires (VignetteExtras), and while the coach
## decides the men shift their weight and the crowd stirs.
## Presentation only, like every vignette: it reads who MatchSim says the call is about
## (the moment's player_id, defender_id, sub_id, the tagger, the match-up) and what the
## ground looks like, and changes nothing. What each choice does is MatchSim's.

const KINDS := ["tired", "duel", "hot", "momentum", "set_shot"]
## Seconds to the freeze, per kind.
const END := {"tired": 3.2, "duel": 3.2, "hot": 3.0, "momentum": 3.0, "set_shot": 2.6}
## Where each scene sits on the ground (oval metres: x across, y along towards your goal)
## and which way its camera looks, so a stand is close behind the men: the tired star walks
## in from the wing with his replacement on the boundary behind him, the duel is in front of
## the goals they kick at, the man kicking a bag runs in off the far wing, the centre waits
## under the far goals. The set shot has no fixed spot: it stands where the call says he
## marked (set_spot). The camera itself is worked out from the picture wanted (_subject).
const STAGE := {
	"tired": {"at": Vector2(60.0, 10.0), "look": Vector2(1.0, 0.0)},
	"duel": {"at": Vector2(5.0, -60.0), "look": Vector2(0.0, -1.0)},
	"hot": {"at": Vector2(34.0, 20.0), "look": Vector2(1.0, 0.35)},
	"momentum": {"at": Vector2(0.0, 0.0), "look": Vector2(0.0, 1.0)},
	"set_shot": {"at": Vector2.ZERO, "look": Vector2(0.0, 1.0)},
}
## The set shot's spots (MatchSim.SET_BANDS_ON, by key): degrees off the line through the
## middle of the goals. Champion Data's cells: straight in front is under 30, a tight angle
## over 60. The distance is the spot's own metres.
const SET_SPOTS := {"close": 0.0, "front": 0.0, "long": 0.0, "angle": 20.0, "pocket": 65.0}

## How far behind the men a duel or hot-hand camera stands, in oval metres (measured
## 2026-11-14: the duel's lens 35 m back on a phone and a PC, the hot hand's 25 m).
const LOOK_ROOM := 36.0
## Where the hot hand's field umpire stands, in scene metres: 5 m behind the chaser's
## start, inside a phone's picture.
const UMP_HOT := Vector2(-1.5, 26.0)
## The man on the mark stands on the mark; the kicker walks back this far from it (the same
## five metres the after-the-siren shot gives him: BroadcastVignette.KICK_BEHIND), on the
## line from the middle of the goals through the mark, so his kick goes over the mark.
const KICKER_BACK := 8.0
## The set shot's camera: this far behind the kicker and this far to the side of his line,
## on the side away from the goals, so the man on the mark shows past his shoulder, smaller
## and further up the ground, and the goals beyond them both: nearer, wider and taller from
## 15 metres than from 55.
const SHOT_D := 16.0
const SHOT_SIDE := 5.5
## The man on the mark jumps on the mark with his arms up, this often (seconds).
const HOP := 1.7

var kind := ""
var _end := 3.0
var _stage: Dictionary = STAGE["tired"]
## The set shot's spot (set_spot) and the ground turned so the kicker looks up the scene at
## the goals.
var spot := {}
## Which side of the goals the set shot is from, as the oval shows it: 1 the kicker's right.
var lean := 1.0
var _to_scene := Transform2D.IDENTITY
## Whether this scene leaves the big screen out (1) or shows it (0), decided once for the
## scene at this size (-1: not yet); see _screen_board.
var _screen_off := -1
var _screen_off_size := Vector2.ZERO
var _ball_box := Rect2()


static func has_scene(k: String) -> bool:
	return k in KINDS


## Where a set shot from that spot (a MatchSim.SET_BANDS_ON key; any other is straight in
## front from 35 metres) is taken, on the ground being drawn (oval metres): the goal (the
## middle of its line), the mark, the kicker, the spot's metres and its angle. Each spot kicks
## at the far goals (+y); side is which side of them it is from (1: the kicker's right).
static func set_spot(band_key: String, side := 1.0) -> Dictionary:
	var key := band_key if SET_SPOTS.has(band_key) else "front"
	var metres := 35.0
	for b in MatchSim.SET_BANDS_ON:
		if str(b["key"]) == key:
			metres = float(b["metres"])
	var angle: float = SET_SPOTS[key]
	var goal := Vector2(0.0, VignetteGround.GOAL_Y)
	var out := Vector2((1.0 if side >= 0.0 else -1.0) * sin(deg_to_rad(angle)), -cos(deg_to_rad(angle)))
	var mark := goal + out * metres
	return {"key": key, "metres": metres, "angle": angle, "goal": goal, "mark": mark,
			"kicker": mark + out * KICKER_BACK}


## shown: the score the match screen's header shows (StoppageVignette.board_of).
func setup_decision(sim: MatchSim, my_side: int, moment: Dictionary, shown := {}) -> void:
	kind = str(moment.get("kind", ""))
	title = str(moment.get("title", ""))
	# Near the goals the stand and the posts rise past the top: they stay off the scoreboard.
	clip_contents = true
	tokens.clear()
	facts = []
	_stage = STAGE.get(kind, STAGE["tired"])
	_end = float(END.get(kind, 3.0))
	weather = VignetteGrade.weather_of(str(sim.get("weather")) if sim.get("weather") != null else "")
	var wet := weather == "wet"
	_board = board_of(sim, my_side, shown)
	for side in range(2):
		var code := str((sim.squads[side] as Squad).code)
		_colours[side] = GameDB.club_colours(code)
		_codes[side] = code
	var them := 1 - my_side
	var me := _pick(sim, my_side, str(moment.get("player_id", "")))
	# The duel and the man kicking a bag stand where the live oval has that man, the camera
	# turned to whichever way has the most players behind him (director, 2026-11-12: "Why
	# not show people in their actual positions?"). The tired star's scene is the
	# interchange gate, wherever he was; the set shot stands where the call says he marked.
	var about := str(moment.get("player_id", ""))
	if kind in ["duel", "hot"] and live_spots.has(about):
		var here: Vector2 = VignetteExtras.keep_in(live_spots[about])
		var others := []
		for id in live_spots:
			if str(id) != about:
				others.append(live_spots[id])
		# The camera stands up to 35 m behind them (the duel's lens on a phone and a PC):
		# a way with no ground for it is not taken.
		_stage = {"at": here, "look": VignetteExtras.best_look(here, others, _stage["look"], LOOK_ROOM)}
	_to_scene = _frame_from(_stage["at"], _stage["look"])
	var focus: Vector2 = _stage["at"]
	# The field umpire stands behind the men, in the camera's picture.
	var near_umpire := Vector2(7.0, 6.0)
	if kind != "tired":
		near_umpire = _to_scene.affine_inverse() * Vector2(-2.9, 12.0) - focus
	match kind:
		"tired":
			# He walks in off the wing, out on his feet; his replacement is up off the bench,
			# stretching on the boundary behind him.
			var star := me
			var sub := _pick(sim, my_side, str(moment.get("sub_id", "")), true)
			_add(star, my_side, true, wet, {"role": "tired", "from": Vector2(-3.6, 7.5), "to": Vector2(-0.9, 0.0),
					"delay": 0.0, "dur": 2.8, "tired": true, "face": "front"})
			_add(sub, my_side, true, wet, {"role": "sub", "from": Vector2(1.7, 8.2), "to": Vector2(1.7, 8.2),
					"delay": 0.0, "dur": 0.1, "face": "front"})
			facts = ["%s's legs are gone." % _surname(GameDB.player_display_name(star))] if not star.is_empty() else []
		"duel":
			# In front of the goals they kick at: the ball comes in over the camera and both
			# men go up at it, facing it.
			var fwd := _pick(sim, them, str(moment.get("player_id", "")))
			var cur_id := str((sim.duels[my_side] as Dictionary).get(str(moment.get("player_id", "")), ""))
			var cur := _pick(sim, my_side, cur_id)
			_add(cur, my_side, true, wet, {"role": "duel_d", "from": Vector2(-3.5, 2.0), "to": Vector2(-1.0, 0.0),
					"delay": 0.0, "dur": 1.2, "face": "front"})
			_add(fwd, them, false, wet, {"role": "duel_f", "from": Vector2(3.5, 2.0), "to": Vector2(1.0, 0.5),
					"delay": 0.15, "dur": 1.2, "face": "front"})
			facts = []
		"hot":
			var stopper = sim.tagger_of(my_side)
			_add(_pick(sim, them, str(moment.get("player_id", ""))), them, false, wet, {"role": "carrier", "from": Vector2(1.0, 18.0), "to": Vector2(-0.6, 0.6),
					"delay": 0.0, "dur": 2.6, "face": "front"})
			if not (stopper is Dictionary) or (stopper as Dictionary).is_empty():
				# No tagger: a midfielder chases, never a defender or ruck drawn by default.
				var mids: Array = (sim.squads[my_side] as Squad).ground.filter(func(p): return str(p["role"]) == "MID")
				stopper = (mids[0] as Dictionary) if not mids.is_empty() else {}
			_add(stopper, my_side, true, wet, {"role": "chaser", "from": Vector2(2.6, 21.0), "to": Vector2(1.4, 3.4),
					"delay": 0.0, "dur": 2.8, "face": "front"})
			# The field umpire trails the chase, behind where both men set off: at (-2.9, 12)
			# he stood 18 px past a phone's left edge (measured 2026-11-14), and at that depth
			# all of a phone's picture is within 3 m of one of the two runs.
			near_umpire = _to_scene.affine_inverse() * UMP_HOT - focus
		"momentum":
			# Their goal, and the walk back: your mids wait on the centre, theirs jog back
			# past them having just kicked it.
			var mine: Array = (sim.squads[my_side] as Squad).ground.filter(
					func(p): return str(p["role"]) in ["MID", "RUCK"]).slice(0, 3)
			var theirs: Array = (sim.squads[them] as Squad).ground.filter(
					func(p): return str(p["role"]) in ["MID", "FWD"]).slice(0, 3)
			for i in range(mine.size()):
				_add(mine[i], my_side, true, wet, {"role": "wait", "from": Vector2(-3.2 + 3.2 * i, 0.0),
						"to": Vector2(-3.2 + 3.2 * i, 0.4 * (i % 2)), "delay": 0.0, "dur": 0.1, "face": "back"})
			for i in range(theirs.size()):
				_add(theirs[i], them, false, wet, {"role": "back_to_square", "from": Vector2(-7.0 + 7.0 * i, 22.0 + 4.0 * i),
						"to": Vector2(-3.6 + 3.6 * i, 5.5 + 1.2 * i), "delay": 0.25 * i, "dur": 2.4, "face": "front"})
		"set_shot":
			var def := _pick(sim, them, str(moment.get("defender_id", "")))
			# From behind him and a little to the side, looking past him at the goals from
			# where the call says he marked: his back to us, the ball in his hands, five
			# metres back from his mark; the man on the mark runs in to the mark, between him
			# and the goals, and jumps with his arms up.
			lean = _oval_lean(my_side)
			spot = set_spot(str(moment.get("band_key", "")), lean)
			_to_scene = _shot_frame(spot)
			focus = spot["mark"]
			_add(me, my_side, true, wet, {"role": "kicker", "from": Vector2.ZERO, "to": Vector2.ZERO,
					"delay": 0.0, "dur": 0.1, "face": "back"})
			if not def.is_empty():
				var on: Vector2 = _to_scene * (spot["mark"] as Vector2)
				_add(def, them, false, wet, {"role": "on_the_mark", "from": on + Vector2(0.6, 5.5), "to": on,
						"delay": 0.0, "dur": 0.9, "face": "front"})
			# The field umpire stands off the mark, on the camera's side of the kick's line.
			near_umpire = _to_scene.affine_inverse() * Vector2(-lean * (SHOT_SIDE + 2.5), KICKER_BACK + 2.0) - focus
	_style_rucks()
	# Everyone else on the ground, where that part of it puts them, and the umpires.
	_cast = VignetteExtras.players(sim, my_side, tokens.map(func(t): return str(t["id"])), focus, wet, false, live_spots) \
			+ VignetteExtras.umpires(focus, near_umpire)
	_place_cast()
	_t = 0.0
	_hold = 0.0
	_idle = 0.0
	_idle_drawn = 0.0
	_frozen = false
	_screen_off = -1
	_shot.clear()
	_dress()
	if _ui == self:
		_ui = VignetteGrade.attach(self, weather, _draw_ui)
	queue_redraw()


## Which side of the goals the oval shows this shot from: 1 when the mark is on the kicker's
## right as he faces the goals, -1 on his left. Read from the oval's own picture of the play
## (where its ball is, which end the kicker's side kicks to this quarter); 1 when the scene
## is shown on its own.
func _oval_lean(side: int) -> float:
	var n: Node = get_parent()
	while n != null:
		var pitch = n.get("_pitch")
		if pitch != null and pitch.get("director") != null:
			var ball = pitch.get("director").get("ball")
			if ball is Dictionary and (ball as Dictionary).get("pos") is Vector2:
				var across := ((ball as Dictionary)["pos"] as Vector2).y
				var up := MatchDirector._dir(side) * (1.0 if int(pitch.get("period")) % 2 == 1 else -1.0)
				if absf(across) > 0.5:
					return 1.0 if across * up > 0.0 else -1.0
			break
		n = n.get_parent()
	return 1.0


## The player of that id on the ground (or the bench); empty when the id is "" or unknown,
## so a scene never names someone MatchSim did not choose.
func _pick(sim: MatchSim, side: int, id: String, bench := false) -> Dictionary:
	var sq: Squad = sim.squads[side]
	for p in (sq.bench if bench else sq.ground) + (sq.ground if bench else sq.bench):
		if str((p as Dictionary)["id"]) == id:
			return p
	return {}


func _add(p: Dictionary, side: int, mine: bool, wet: bool, extra: Dictionary) -> void:
	if p.is_empty():
		return
	var tok := {"side": side, "mine": mine, "slot": "X", "id": str(p["id"]), "tall": false,
			"look": GameDB.figure_look(p, wet), "height_cm": float(p.get("height_cm", 0.0)),
			"name": _surname(GameDB.player_display_name(p)), "num": int(p["num"]), "tired": false}
	tokens.append(tok.merged(extra, true))


## No rucks here: the base's styling is skipped.
func _style_rucks() -> void:
	pass


func token_of(role: String) -> Dictionary:
	for t in tokens:
		if str(t.get("role", "")) == role:
			return t
	return {}


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------
func finish_now() -> void:
	_t = _end
	_freeze()


func _process(delta: float) -> void:
	if _frozen:
		_after_freeze(delta)
		return
	_t += delta
	if _t >= _end:
		_t = _end
		_freeze()
	queue_redraw()


func _freeze_at() -> float:
	return _end


## The men keep shifting their weight and the crowd stirs while the coach decides. Not the
## duel: it freezes with both men and the ball in the air, and nothing moves round that.
func _idles() -> bool:
	return kind != "duel"


# ---------------------------------------------------------------------------
# Where everyone is and what he is doing
# ---------------------------------------------------------------------------
func _pos(t: Dictionary) -> Vector2:
	var k := clampf((_t - float(t["delay"])) / float(t["dur"]), 0.0, 1.0)
	return (t["from"] as Vector2).lerp(t["to"], _ease(k) if str(t["role"]) != "tired" else k * (2.0 - k) * 0.6 + k * 0.4)


func _moving(t: Dictionary) -> bool:
	var k := (_t - float(t["delay"])) / float(t["dur"])
	return k > 0.0 and k < 0.97 and (t["from"] as Vector2) != (t["to"] as Vector2)


## How high the man on the mark's jump is now, 0 (on the ground) to 1: up as the scene
## freezes, then again every HOP seconds while the coach decides.
func _hop(t: Dictionary) -> float:
	if _t < float(t["delay"]) + float(t["dur"]):
		return 0.0
	var u := fposmod(clock() - _end + HOP * 0.2, HOP) / HOP
	return sin(PI * u / 0.4) if u < 0.4 else 0.0


## The contest at the top: both men go up together at the freeze, as the ruckmen do. The
## man on the mark jumps on the spot.
func _lift(t: Dictionary) -> float:
	var role := str(t.get("role", ""))
	if role in ["duel_d", "duel_f"]:
		var start := _end - 1.0 + (0.06 if role == "duel_f" else 0.0)
		return 0.9 * _ease(clampf((_t - start) / 0.7, 0.0, 1.0))
	if role == "on_the_mark":
		return 0.5 * _hop(t)
	return 0.0


func _frame(t: Dictionary, lift: float, at := Vector2.ZERO, back := false) -> Array:
	if t.is_empty() or t.has("extra"):
		return super(t, lift, at, back)
	var role := str(t["role"])
	var now := clock()
	var cycle := int(now * 3.0 * _rate(t, 0.7, 1.15) + float(t["num"]) * 0.37) % 3
	match role:
		"tired":
			if _moving(t):
				# Out on his feet: a slow stride.
				return ["walk", int(_t * 5.0) % 8, false, "front_r"]
			# Stopped, heaving: his weight shifts slowly.
			return ["ready", int(now * 1.3) % 3, false, "front"]
		"sub":
			# Stripped and stretching on the boundary, ready to go on.
			return ["ready_b", cycle, false, "front"]
		"duel_d", "duel_f":
			if lift > 0.0:
				var k := clampf(lift / 0.9, 0.0, 1.0)
				return ["leap", int(roundf(k * 5.0)), role == "duel_f", "front"]
			if _moving(t):
				return ["jog", int(_t * 13.0 / TAU * 8.0 + float(t["num"])) % 8, false, "front"]
			return ["ready", cycle, role == "duel_f", "front"]
		"carrier":
			return ["carrier", int(_t * 10.0) % 8, false, "front"] if _moving(t) else ["ready", cycle, false, "front"]
		"chaser":
			return ["jog", int(_t * 13.0 / TAU * 8.0 + float(t["num"])) % 8, false, "front"] if _moving(t) \
					else ["ready_turn", cycle, true, "front"]
		"wait":
			# Hands on hips at the centre, watching them come back.
			var pick := _watch_pick(t, at, true, Vector2(0.0, 12.0))
			return [pick[0], pick[1], pick[2], "back"]
		"back_to_square":
			if _moving(t):
				return ["jog", int(_t * 11.0 / TAU * 8.0 + float(t["num"])) % 8, int(t["num"]) % 2 == 0, "front"]
			# They have just kicked it: one claps his mates on, the others set up again.
			if int(t["num"]) % 2 == 0 and VignetteFigures.has(_body(t), "clap", "side_l"):
				return ["clap", int(now * 6.0) % 4, false, "side_l"]
			return ["ready", cycle, false, "front"]
		"kicker":
			return ["ready", cycle, false, "back"]
		"on_the_mark":
			if _moving(t):
				return ["jog", int(_t * 9.0 / TAU * 8.0) % 8, false, "front"]
			if lift > 0.0:
				return ["leap", int(roundf(clampf(lift / 0.5, 0.0, 1.0) * 5.0)), false, "front"]
			return ["ready", cycle, false, "front"]
	return super(t, lift, at, back)


func _look_at(_t_: Dictionary) -> Vector2:
	return Vector2(0.0, 30.0)


## Whose names show at the freeze: the men the call is about.
func _named() -> Array:
	return tokens.filter(func(t): return not (str(t["role"]) in ["wait", "back_to_square"]) \
			and (str(t["role"]) != "sub" or kind == "tired"))


## The cast watch the men the call is about.
func _cast_focus() -> Vector2:
	return Vector2(0.0, 0.5)


## The cast keep off the scene's own ground: the few metres round its men, and at a set
## shot the protected ground round the kicker and the man on the mark.
func _cast_fits(at: Vector2) -> bool:
	if kind == "set_shot":
		# ...as far as ten metres past the mark: beyond it the packs wait for the kick.
		return absf(at.x) > 7.0 or at.y > KICKER_BACK + 10.0
	return at.y > 6.0 or absf(at.x) > 7.0


# ---------------------------------------------------------------------------
# The camera and the ground
# ---------------------------------------------------------------------------
## What each scene's freeze frames (StoppageVignette._subject): two or three men filling
## the picture, the camera's distance found so the stand behind them fills the top.
func _subject() -> Dictionary:
	match kind:
		"duel":
			return {"near": 0.0, "mid": 0.0, "half": 1.9, "top": 5.4, "tall": 0.62, "d": 0.0, "x": 0.0}
		"hot":
			return {"near": 0.6, "mid": 0.4, "half": 2.0, "top": 3.4, "tall": 0.5, "d": 0.0, "x": 0.0}
		"momentum":
			return {"near": 0.0, "mid": 0.0, "half": 4.2, "top": 3.4, "tall": 0.42, "d": 0.0, "x": 0.0}
		"set_shot":
			var x := -lean * SHOT_SIDE
			var across := _shot_across(x)
			return {"near": 0.0, "mid": across.x, "half": across.y, "top": 4.0, "tall": 0.5, "d": SHOT_D, "x": x,
					"feet": 0.05}
	return {"near": 0.0, "mid": 0.35, "half": 2.2, "top": 3.4, "tall": 0.5, "d": 0.0, "x": 0.0}


## What the set shot's picture holds across, from a camera x metres to the side: from the
## kicker's outside shoulder to the goal post furthest from him, measured where the kicker
## stands (x: the middle of that; y: half its width, with a little room).
func _shot_across(x: float) -> Vector2:
	var side := 1.0 if x >= 0.0 else -1.0
	var metres := float(spot.get("metres", 35.0))
	var narrow := cos(deg_to_rad(float(spot.get("angle", 0.0))))
	var post := x + (side * 0.5 * VignetteGround.GOAL_GAP * narrow - x) * SHOT_D / (metres + KICKER_BACK + SHOT_D)
	var shoulder := -side * 0.75
	# (From a pocket the four posts fan out across the picture: a little wider, so the camera
	# has room to stand every post clear of both men.)
	var fan := pow(sin(deg_to_rad(float(spot.get("angle", 0.0)))), 2.0)
	return Vector2((post + shoulder) * 0.5, absf(post - shoulder) * 0.5 + 0.3 + 0.8 * fan)


## The set shot's camera stays on its side of the kicker's line, at least a few metres off.
func _cam_steps() -> Array:
	if kind != "set_shot":
		return super()
	return super().filter(func(step): return -lean * (-lean * SHOT_SIDE + float(step)) >= 3.5)


## A set shot's picture is good when no post tops a man and both goal posts are in it.
func _shot_good() -> bool:
	if kind != "set_shot":
		return super()
	_shot["mid"] = _shot_across(float(_shot["x"])).x
	_apply_camera(_t, _hold)
	if not posts_clear():
		return false
	var cam := ground_cam()
	for i in [-0.5, 0.5]:
		var foot := cam.oval(Vector2(i * VignetteGround.GOAL_GAP, VignetteGround.GOAL_Y))
		if foot.z <= 0.0 or foot.x < 6.0 or foot.x > size.x - 6.0:
			return false
	return true


func _clear_posts() -> void:
	super()
	if kind == "set_shot":
		# The camera may have stepped across: the picture is centred again from where it is.
		_shot["mid"] = _shot_across(float(_shot["x"])).x
		_apply_camera(_t, _hold)


## A slow push in over the play, then the freeze's last move: the lens to its settled
## length, the picture tilted so the men stand clear of the call.
func _apply_camera(t: float, hold_t: float) -> void:
	var k := clampf(t / _end, 0.0, 1.0)
	var punch := _ease(clampf(hold_t / 0.4, 0.0, 1.0))
	var d: float = _shot["d"]
	var fit := _freeze_fit()
	_zoom = lerpf(lerpf(0.88, 0.96, k), fit.x, punch)
	_cam_d = d - float(_shot["near"])
	_cam_h = _shot["h"]
	_cam_x = _shot["x"]
	_focal = float(_shot["s"]) * d * _zoom
	_pan = _focal * (float(_shot["mid"]) - _cam_x) / d
	_horizon = lerpf(float(_shot["feet"]), fit.y, punch) - _focal * _cam_h / d


## This scene's spot on the ground as the scene's origin, its camera looking up the scene.
func _ground_to_scene() -> Transform2D:
	return _to_scene


## Close to the goals the big screen rises under the title bar, or past the side of the
## picture, and half a screen reads as a fault. A scene whose camera would cut into it at any
## point, from the cut-in to the settled freeze, leaves it out from first frame to last, so it
## never vanishes mid-scene.
func _screen_board(_cam: VignetteGround.Cam) -> Dictionary:
	if _screen_off < 0 or _screen_off_size != size:
		_screen_off_size = size
		var cut := false
		for i in range(21):
			cut = cut or screen_cut_at(_end * float(i) / 20.0, 0.0)
		for i in range(1, 9):
			cut = cut or screen_cut_at(_end, 0.05 * float(i))
		_screen_off = 1 if cut else 0
	# Left out, the board still says which end the breeze blows to: the stand flags read it.
	return {"off": true, "wind": _board.get("wind", 1)} if _screen_off == 1 else _board


## Whether the big screen would be cut, by the title bar (into its writing, below its top
## 15%) or by either side of the picture, with the camera where it is at that time into the
## play-in and that far into the freeze's punch.
func screen_cut_at(t: float, hold: float) -> bool:
	shot()
	# The picture tilts up as the call rises: judged for the call as it is and for a tall one
	# (half the screen), so the answer is the same before the call exists as after.
	var room := call_room
	var cut := false
	for tall in [room, maxf(room, size.y * 0.5)]:
		call_room = tall
		_apply_camera(t, hold)
		var r := VignetteGround.screen_rect(ground_cam())
		cut = cut or (r.has_area() and (r.position.y + r.size.y * 0.15 < size.y * 0.075 or r.position.x < 0.0 or r.end.x > size.x))
	call_room = room
	_apply_camera(_t, _hold)
	return cut


## A scene's ground: at is the scene's origin and the scene's +y runs along look, so a
## camera behind the origin looks that way up the ground.
static func _frame_from(at: Vector2, look: Vector2) -> Transform2D:
	var fwd := look.normalized()
	var right := Vector2(fwd.y, -fwd.x)
	return Transform2D(Vector2(right.x, fwd.x), Vector2(right.y, fwd.y), Vector2(-at.dot(right), -at.dot(fwd)))


## The set shot's ground: the kicker's spot is the scene's origin and the scene's +y runs
## from him through the middle of the goals, so the camera behind him looks down his line.
static func _shot_frame(s: Dictionary) -> Transform2D:
	return _frame_from(s["kicker"], (s["goal"] as Vector2) - (s["kicker"] as Vector2))


## Where a token stands on the ground (oval metres) right now.
func spot_of(t: Dictionary) -> Vector2:
	return _ground_to_scene().affine_inverse() * _pos(t)


## Where the camera stands on the ground (oval metres).
func camera_spot() -> Vector2:
	shot()
	return _ground_to_scene().affine_inverse() * Vector2(float(_shot["x"]), float(_shot["near"]) - float(_shot["d"]))


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
func _draw() -> void:
	_set_camera()
	_draw_ground()
	var lights := VignetteAtmos.draw_back(self, ground_cam(), Rect2(Vector2.ZERO, size), weather)
	var figures := []
	for t in tokens:
		figures.append({"at": _pos(t), "t": t})
	for e in _cast:
		figures.append({"at": e["at"], "t": e})
	figures.sort_custom(func(a, b): return (a["at"] as Vector2).y > (b["at"] as Vector2).y)
	_ball_box = Rect2()
	for f in figures:
		# The kicker has his back to us: the ball in his hands is in front of him, so it
		# goes down before he does.
		if kind == "set_shot" and str(f["t"].get("role", "")) == "kicker":
			_draw_ball_scene()
		_draw_figure(f["at"], f["t"])
	if kind != "set_shot":
		_draw_ball_scene()
	VignetteWeather.draw_air(self, Rect2(Vector2.ZERO, size), clock(), weather)
	VignetteAtmos.draw_front(self, Rect2(Vector2.ZERO, size), lights, weather, clock())
	if _frozen:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.18), true)
		if _hold < 0.15:
			draw_rect(Rect2(Vector2.ZERO, size), Color(1, 1, 1, 0.5 * (1.0 - _hold / 0.15)), true)
	if _ui == self:
		_draw_ui()


## Where a token's palm is on screen right now (hand 0 his left, 1 his right), the way
## _draw_figure places the figure, from the palms recorded with the figure.
func palm_of(t: Dictionary, hand := 0) -> Vector2:
	var at := _pos(t)
	var lift := _lift(t)
	var base := _project(at, lift)
	var pick := _frame(t, lift, at, bool(t["mine"]))
	var facing: String = str(pick[3]) if pick.size() > 3 else str(t["face"])
	var build := _body(t)
	if not VignetteFigures.has(build, pick[0], facing):
		build = "average"
	var info := VignetteFigures.strip(build, pick[0], facing)
	var frame := clampi(int(pick[1]), 0, int(info["frames"]) - 1)
	var h := VignetteFigures.hands(info, frame)
	if h.is_empty():
		return Vector2.INF
	var k: float = base.z * FIGURE / VignetteFigures.PX_PER_M * (0.96 if bool(t["tired"]) else 1.0)
	var rel: Vector2 = ((h[hand] as Vector2) - Vector2(info["pivot"][0], info["pivot"][1])) * k
	if bool(pick[2]):
		rel.x = -rel.x
	return Vector2(base.x, base.y) + rel


## The ball: in the kicker's hands at the mark (set shot), or kicked in to the duel and
## met at the top by both men. Never loose of the player using it.
func _draw_ball_scene() -> void:
	var centre := Vector2.INF
	var r := 0.0
	if kind == "set_shot":
		var t := token_of("kicker")
		if t.is_empty():
			return
		var a := palm_of(t, 0)
		var b := palm_of(t, 1)
		if a == Vector2.INF or b == Vector2.INF:
			return
		centre = (a + b) * 0.5
		r = maxf(3.0, 0.2 * _project(_pos(t)).z * FIGURE)
	elif kind == "duel":
		var d := token_of("duel_d")
		var f := token_of("duel_f")
		if d.is_empty() or f.is_empty():
			return
		var pd := palm_of(d, 1)
		var pf := palm_of(f, 0)
		var s := _project(_pos(d))
		r = maxf(3.0, 0.2 * s.z * FIGURE)
		if pd == Vector2.INF or pf == Vector2.INF:
			return
		var meet := (pd + pf) * 0.5 + Vector2(0.0, -r * 0.6)
		# Kicked in from the middle of the ground, behind the camera: it comes down over the
		# top of the picture, big and close, and is met as both men reach the top.
		var k := _ease(clampf(_t / (_end - 0.3), 0.0, 1.0))
		var from := Vector2(size.x * 0.5 + (meet.x - size.x * 0.5) * 0.4, -r * 3.0)
		centre = from.lerp(meet, k)
		r = lerpf(r * 2.4, r, k)
		_ball_box = Rect2(centre - Vector2(r + 4.0, r + 4.0), Vector2(r + 4.0, r + 4.0) * 2.0)
	if centre == Vector2.INF:
		return
	VignetteBall.draw(self, centre, 2.0 * r, _t, kind == "duel" and not _frozen)


## At the freeze: who is who, pinned to the heads of the men the call is about.
func _draw_names() -> void:
	_draw_tags(_named(), [_ball_box] if _ball_box.has_area() else [])
