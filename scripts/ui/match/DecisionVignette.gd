class_name DecisionVignette
extends StoppageVignette
## A staged close-up for each in-match call that was still a text card (TODO row 13):
## a star running on empty (tired), a forward getting on top (duel), a midfielder
## kicking a bag (hot), a run of goals against (momentum), a set shot at goal
## (set_shot). The late centre-bounce call has its own scene (StoppageVignette).
##
## The match cuts to a low camera, the players the call is about move into place and
## the frame freezes; the call slides up over it (MatchScene._show_decision_moment).
## Presentation only, like every vignette: it reads who MatchSim says the call is about
## (the moment's player_id, defender_id, sub_id, the tagger, the match-up) and what the
## ground looks like, and changes nothing. What each choice does is MatchSim's.
##
## Behind Features "decision_scenes" (default off): off, the call is the text card it was.

const KINDS := ["tired", "duel", "hot", "momentum", "set_shot"]
## Seconds to the freeze, per kind.
const END := {"tired": 3.2, "duel": 3.2, "hot": 3.0, "momentum": 3.0, "set_shot": 2.6}
## Where each scene sits on the ground (oval metres: x across, y along towards your goal)
## and the camera's distance behind and height above that spot.
const STAGE := {
	"tired": {"at": Vector2(46.0, 10.0), "d": 6.5, "h": 1.5, "x": 0.0, "zoom": 1.0},
	"duel": {"at": Vector2(8.0, -52.0), "d": 9.0, "h": 2.2, "x": 0.0, "zoom": 1.0},
	"hot": {"at": Vector2(0.0, 18.0), "d": 6.0, "h": 1.6, "x": 0.0, "zoom": 1.0},
	"momentum": {"at": Vector2(0.0, 0.0), "d": 14.0, "h": 3.2, "x": 0.0, "zoom": 1.0},
	"set_shot": {"at": Vector2(3.0, 40.0), "d": 6.5, "h": 1.7, "x": 0.0, "zoom": 1.0},
}

var kind := ""
var _end := 3.0
var _stage: Dictionary = STAGE["tired"]
var _hold_ball := {}              # {id, hand} when a player has the ball in his hands
var _fly := {}                    # the duel's ball: {from: Vector2, to_id: [id, id]}


static func has_scene(k: String) -> bool:
	return k in KINDS


func setup_decision(sim: MatchSim, my_side: int, moment: Dictionary) -> void:
	kind = str(moment.get("kind", ""))
	title = str(moment.get("title", ""))
	tokens.clear()
	facts = []
	_hold_ball = {}
	_fly = {}
	_stage = STAGE.get(kind, STAGE["tired"])
	_end = float(END.get(kind, 3.0))
	weather = str(sim.get("weather")) if sim.get("weather") != null else ""
	var wet := weather == "wet"
	_board = {"codes": [str((sim.squads[0] as Squad).code), str((sim.squads[1] as Squad).code)],
			"goals": [sim.goals(0), sim.goals(1)], "behinds": [sim.behinds(0), sim.behinds(1)],
			"q": sim.current_quarter}
	for side in range(2):
		var code := str((sim.squads[side] as Squad).code)
		_colours[side] = GameDB.club_colours(code)
		_codes[side] = code
	var them := 1 - my_side
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%s|%s|%d" % [kind, str(moment.get("player_id", "")), sim.current_minute])
	var me := _pick(sim, my_side, str(moment.get("player_id", "")))
	match kind:
		"tired":
			var star := me
			var sub := _pick(sim, my_side, str(moment.get("sub_id", "")), true)
			_add(star, my_side, true, wet, {"role": "tired", "from": Vector2(-6.0, 12.0), "to": Vector2(-1.1, 0.8),
					"delay": 0.0, "dur": 2.8, "tired": true, "face": "front"})
			_add(sub, my_side, true, wet, {"role": "sub", "from": Vector2(2.4, 4.0), "to": Vector2(2.4, 4.0),
					"delay": 0.0, "dur": 0.1, "face": "front"})
			facts = ["%s's legs are gone." % _surname(GameDB.player_display_name(star))] if not star.is_empty() else []
		"duel":
			var fwd := _pick(sim, them, str(moment.get("player_id", "")))
			var cur_id := str((sim.duels[my_side] as Dictionary).get(str(moment.get("player_id", "")), ""))
			var cur := _pick(sim, my_side, cur_id)
			_add(cur, my_side, true, wet, {"role": "duel_d", "from": Vector2(-3.5, 2.0), "to": Vector2(-1.1, 0.0),
					"delay": 0.0, "dur": 1.2, "face": "back"})
			_add(fwd, them, false, wet, {"role": "duel_f", "from": Vector2(3.5, 2.0), "to": Vector2(1.1, 0.6),
					"delay": 0.15, "dur": 1.2, "face": "back"})
			facts = []
		"hot":
			var stopper = sim.tagger_of(my_side)
			_add(_pick(sim, them, str(moment.get("player_id", ""))), them, false, wet, {"role": "carrier", "from": Vector2(1.0, 26.0), "to": Vector2(-0.3, 1.0),
					"delay": 0.0, "dur": 2.6, "face": "front"})
			if not (stopper is Dictionary) or (stopper as Dictionary).is_empty():
				stopper = _pick(sim, my_side, "")
			_add(stopper, my_side, true, wet, {"role": "chaser", "from": Vector2(2.6, 29.0), "to": Vector2(1.9, 4.0),
					"delay": 0.0, "dur": 2.8, "face": "front"})
		"momentum":
			# Their goal, and the walk back: your mids wait on the centre, theirs jog back
			# past them having just kicked it.
			var mine: Array = (sim.squads[my_side] as Squad).ground.filter(
					func(p): return str(p["role"]) in ["MID", "RUCK"]).slice(0, 3)
			var theirs: Array = (sim.squads[them] as Squad).ground.filter(
					func(p): return str(p["role"]) in ["MID", "FWD"]).slice(0, 3)
			for i in range(mine.size()):
				_add(mine[i], my_side, true, wet, {"role": "wait", "from": Vector2(-4.0 + 4.0 * i, -6.0),
						"to": Vector2(-4.0 + 4.0 * i, -6.0 + 0.4 * (i % 2)), "delay": 0.0, "dur": 0.1, "face": "back"})
			for i in range(theirs.size()):
				_add(theirs[i], them, false, wet, {"role": "back_to_square", "from": Vector2(-7.0 + 7.0 * i, 24.0 + 4.0 * i),
						"to": Vector2(-5.0 + 5.0 * i, 5.0 + 1.5 * i), "delay": 0.25 * i, "dur": 2.4, "face": "front"})
		"set_shot":
			var def := _pick(sim, them, str(moment.get("defender_id", "")))
			# Over the man on the mark's shoulder: the kicker faces us holding the ball
			# (the goals are behind the camera; see _ground_to_scene).
			_add(me, my_side, true, wet, {"role": "kicker", "from": Vector2(0.6, 7.5), "to": Vector2(0.6, 7.5),
					"delay": 0.0, "dur": 0.1, "face": "front"})
			if not def.is_empty():
				_add(def, them, false, wet, {"role": "on_the_mark", "from": Vector2(-1.0, 9.0), "to": Vector2(-1.0, 2.6),
						"delay": 0.0, "dur": 0.9, "face": "back"})
			_hold_ball = {"id": str(me.get("id", "")), "kicker": true}
	_style_rucks()
	_t = 0.0
	_hold = 0.0
	_frozen = false
	_dress()
	queue_redraw()


## The player of that id on the ground (or the bench), else the first on the ground of the side.
func _pick(sim: MatchSim, side: int, id: String, bench := false) -> Dictionary:
	var sq: Squad = sim.squads[side]
	for p in (sq.bench if bench else sq.ground) + (sq.ground if bench else sq.bench):
		if str((p as Dictionary)["id"]) == id:
			return p
	return (sq.ground[0] as Dictionary) if not sq.ground.is_empty() and id == "" else {}


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
		if _hold < 0.4:
			_hold += delta
			queue_redraw()
		return
	_t += delta
	if _t >= _end:
		_t = _end
		_freeze()
	queue_redraw()


# ---------------------------------------------------------------------------
# Where everyone is and what he is doing
# ---------------------------------------------------------------------------
func _pos(t: Dictionary) -> Vector2:
	var k := clampf((_t - float(t["delay"])) / float(t["dur"]), 0.0, 1.0)
	return (t["from"] as Vector2).lerp(t["to"], _ease(k) if str(t["role"]) != "tired" else k * (2.0 - k) * 0.6 + k * 0.4)


func _moving(t: Dictionary) -> bool:
	var k := (_t - float(t["delay"])) / float(t["dur"])
	return k > 0.0 and k < 0.97 and (t["from"] as Vector2) != (t["to"] as Vector2)


## The contest at the top: both men go up together at the freeze, as the ruckmen do.
func _lift(t: Dictionary) -> float:
	if str(t["role"]) in ["duel_d", "duel_f"]:
		var start := _end - 1.0 + (0.06 if str(t["role"]) == "duel_f" else 0.0)
		return 0.9 * _ease(clampf((_t - start) / 0.7, 0.0, 1.0))
	return 0.0


func _frame(t: Dictionary, lift: float, at := Vector2.ZERO, back := false) -> Array:
	var role := str(t["role"])
	var face := str(t["face"])
	var cycle := int(_t * 3.0 * _rate(t, 0.7, 1.15) + float(t["num"]) * 0.37) % 3
	match role:
		"tired":
			if _moving(t):
				# Out on his feet: a slow stride.
				return ["walk", int(_t * 5.0) % 8, false, "front_r"]
			return ["idle", 0, false, "front"]
		"sub":
			# Stripped and stretching on the boundary, ready to go on.
			return ["ready_b", cycle, false, "front"]
		"duel_d", "duel_f":
			if lift > 0.0:
				var k := clampf(lift / 0.9, 0.0, 1.0)
				return ["leap", int(roundf(k * 5.0)), role == "duel_f", "back"]
			if _moving(t):
				return ["jog", int(_t * 13.0 / TAU * 8.0 + float(t["num"])) % 8, false, "back"]
			return ["ready", cycle, role == "duel_f", "back"]
		"carrier":
			return ["carrier", int(_t * 10.0) % 8, false, "front"] if _moving(t) else ["idle", 0, false, "front"]
		"chaser":
			return ["jog", int(_t * 13.0 / TAU * 8.0 + float(t["num"])) % 8, false, "front"] if _moving(t) \
					else ["ready", cycle, false, "front"]
		"wait":
			return ["idle", 0, false, "back"]
		"back_to_square":
			return ["jog", int(_t * 11.0 / TAU * 8.0 + float(t["num"])) % 8, int(t["num"]) % 2 == 0, "front"] if _moving(t) \
					else ["celebrate", 0, false, "front"] if int(t["num"]) % 2 == 0 else ["ready", cycle, false, "front"]
		"kicker":
			return ["ready", cycle, false, "front"]
		"on_the_mark":
			return ["jog", int(_t * 9.0 / TAU * 8.0) % 8, false, "back"] if _moving(t) else ["ready", cycle, false, "back"]
	return super(t, lift, at, back)


func _look_at(_t_: Dictionary) -> Vector2:
	return Vector2(0.0, 30.0)


# ---------------------------------------------------------------------------
# The camera and the ground
# ---------------------------------------------------------------------------
func _set_camera() -> void:
	var punch := _ease(clampf(_hold / 0.4, 0.0, 1.0))
	_cam_d = float(_stage["d"])
	_cam_h = float(_stage["h"])
	_cam_x = float(_stage["x"])
	var base := size.y * 0.7 * 1.2 if size.x > size.y else maxf(size.x * 1.5, size.y * 0.7)
	# A slow push in over the scene, a last punch on the freeze.
	_zoom = lerpf(1.0, 1.12, clampf(_t / _end, 0.0, 1.0)) * (1.0 + 0.06 * punch) * float(_stage["zoom"])
	_focal = base * _zoom
	_pan = 0.0
	# The subject sits in the upper half, clear of the call that takes the bottom.
	var at: Array = [0.62, 0.56] if size.x > size.y else [0.66, 0.6]
	_horizon = size.y * lerpf(at[0], at[1], punch) - _focal * _cam_h / _cam_d


## This scene's spot on the ground as the scene's origin.
func _ground_to_scene() -> Transform2D:
	var at: Vector2 = _stage["at"]
	if kind == "set_shot":
		# Turned about: the camera looks back up the ground from the goal side.
		return Transform2D(Vector2(-1, 0), Vector2(0, -1), at)
	return Transform2D(Vector2(1, 0), Vector2(0, 1), -at)


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
func _draw() -> void:
	_set_camera()
	var fade := clampf(_t / CUT_IN, 0.0, 1.0) if not _frozen else 1.0
	_draw_ground()
	var figures := []
	for t in tokens:
		figures.append({"at": _pos(t), "t": t})
	figures.sort_custom(func(a, b): return (a["at"] as Vector2).y > (b["at"] as Vector2).y)
	for f in figures:
		_draw_figure(f["at"], f["t"])
	_draw_ball_scene()
	VignetteWeather.draw_air(self, Rect2(Vector2.ZERO, size), _t, weather)
	if _frozen:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.18), true)
		if _hold < 0.15:
			draw_rect(Rect2(Vector2.ZERO, size), Color(1, 1, 1, 0.5 * (1.0 - _hold / 0.15)), true)
		_draw_decision_names()
	_draw_bars(fade)
	if fade < 1.0:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 1.0 - fade), true)


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
		# In from the centre of the ground over the first two seconds, then met.
		var k := _ease(clampf(_t / (_end - 0.3), 0.0, 1.0))
		var from := Vector2(size.x * 0.5, _horizon - size.y * 0.1)
		centre = from.lerp(meet, k) + Vector2(0.0, -sin(k * PI) * size.y * 0.18)
		r = lerpf(r * 0.4, r, k)
	if centre == Vector2.INF:
		return
	VignetteBall.draw(self, centre, 2.0 * r, _t, kind == "duel" and not _frozen)


## At the freeze: who is who, over the heads of the men the call is about.
func _draw_decision_names() -> void:
	var font: Font = UiKit.BOLD
	var fs := int(clampf(size.x / 26.0, 12.0, 17.0))
	var placed: Array[Rect2] = []
	for t in tokens:
		if str(t["role"]) in ["wait", "back_to_square", "sub"] and kind != "tired":
			continue
		var head := _project(_pos(t), _lift(t) + _figure_top(t))
		var name := str(t["name"])
		var nw := font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var y := head.y - 6.0 - fs
		if head.y < size.y * 0.24:
			# Too near the scoreboard: the name goes under his feet instead.
			y = _project(_pos(t), _lift(t)).y + 6.0
		var box := Rect2(Vector2(clampf(head.x - nw * 0.5, 4.0, size.x - nw - 4.0), y), Vector2(nw, fs + 2))
		var tries := 0
		while tries < 4 and placed.any(func(q): return q.intersects(box)):
			box.position.y -= fs + 3
			tries += 1
		placed.append(box)
		var p := Vector2(box.position.x, box.position.y + fs)
		draw_string(font, p + Vector2(1, 1), name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0, 0, 0, 0.6))
		draw_string(font, p, name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1, 1, 1))
