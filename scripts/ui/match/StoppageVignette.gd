class_name StoppageVignette
extends Control
## A staged centre bounce, for the late-game centre-bounce call (ARD-M8-007
## prototype). The match cuts to the broadcast camera behind your end, wide on
## the centre square: the real rucks and centre-square midfielders jog into
## their set-up, a tired one lagging behind the rest, and the umpire walks in
## with the ball. Only once the whole stoppage has been seen does the lens push
## in: he bounces it, the rucks go up - and it freezes at the top of the
## contest for the call (row T2.48: establish the stoppage before the close-up).
##
## Presentation only: it reads MatchSim's state (who is on the ground, their
## legs, how the stoppages have gone) and changes nothing. What the call does
## is decided by MatchSim when it is made.

signal ready_for_call

## How much of the bottom of the scene the call covers once it is up (MatchScene
## sets it as the call slides up): a name drawn under a man's feet stays above it.
var call_room := 0.0

## Only the stoppage: the ruck and the three centre-square midfielders a side.
const SLOTS := ["R", "C", "RR", "RV"]
## Beats of the scene, in seconds.
const CUT_IN := 0.35
const UMP_IN := [1.2, 2.6]
const BALL_UP := 3.5       # the umpire bounces it
const RUN_IN := [3.5, 4.05]
const FREEZE := 4.4
## The wide shot holds until the umpire lifts the ball; the push-in runs from here to the freeze.
const PUSH_IN := BALL_UP - 0.7
## Legs below this are running on empty (MatchNotes.EMPTY).
const EMPTY := 50.0
## Players are drawn larger than life so a phone can read them.
const FIGURE := 1.6
## The camera sits a little to one side of the corridor, over a shoulder.
const CAM_X := -3.0
## The field umpire's fluoro shirt: saturated, so it never reads as skin at a distance.
const UMPIRE := Color(0.66, 0.96, 0.08)
## The footballers are pre-rendered figures recoloured for each club
## (VignetteFigures.gd has the sheet's layout, figure.gdshader the recolouring).
const FIGURE_SHADE := preload("res://assets/vignette/figures_shade.png")
const FIGURE_MASK := preload("res://assets/vignette/figures_mask.png")
const FIGURE_DESIGN := preload("res://assets/vignette/figures_design.png")
const FIGURE_SHADER := preload("res://assets/vignette/figure.gdshader")
## Digits the shader prints players' numbers with, on the guernsey itself.
const FIGURE_DIGITS := preload("res://assets/vignette/figures_digits.png")
## Kits in the shader's palette: the two sides, then the umpire.
const UMPIRE_KIT := 2

## Tests switch this on to see which figure frames the vignettes ask for. A
## frame past the end of a move would otherwise freeze on its last frame
## without a word. Off in play.
static var log_frames := false
static var frame_log: Array = []  # {anim, facing, frames, wanted, info: the strip drawn}
## ... and which hair they draw over the figures: {style, texture}.
static var hair_log: Array = []
## The faces drawn while log_frames is on.
static var face_log: Array = []
## The premiership ink drawn while log_frames is on.
static var ink_log: Array = []

var tokens: Array = []      # {side, mine, slot, id, tall, look, name, num, tired, from, to, delay, dur}
var facts: Array = []       # one or two lines of commentary, no numbers
var title := ""
var _colours := [[], []]
var _codes := ["", ""]
var _board := {}           # the match's score, for the big screen at the end of the ground
var _kits := []            # both sides' guernseys, as dressed
## The day's weather (MatchSim.weather; VignetteWeather): how the ground and air look.
var weather := ""
var _t := 0.0
var _frozen := false
var _hold := 0.0            # time since the freeze, for the last push-in


## The big screen's board for a call scene: both clubs, the score (the one the header
## shows when the match screen hands it over, else the match's own), the quarter, and the
## end the breeze blows to. Your side kicks to the scene's +y end, so the breeze blows
## there (+1) in a quarter your side kicks with it and to the other end (-1) otherwise.
## Read only: nothing here touches the match.
static func board_of(sim: MatchSim, my_side: int, shown := {}) -> Dictionary:
	var goals: Array = shown.get("goals", [])
	var behinds: Array = shown.get("behinds", [])
	if goals.size() < 2 or behinds.size() < 2:
		goals = [sim.goals(0), sim.goals(1)]
		behinds = [sim.behinds(0), sim.behinds(1)]
	return {"codes": [str((sim.squads[0] as Squad).code), str((sim.squads[1] as Squad).code)],
			"goals": [int(goals[0]), int(goals[1])], "behinds": [int(behinds[0]), int(behinds[1])],
			"q": sim.current_quarter, "wind": 1 if sim.with_breeze(my_side) else -1}


## shown: the score the match screen's header shows ({goals: [home, away], behinds:
## [home, away]}), so the big screen never runs ahead of it; empty, the match's own.
func setup(sim: MatchSim, my_side: int, heading := "", shown := {}) -> void:
	title = heading
	tokens.clear()
	# The day's weather, when MatchSim has one; more of them wear long sleeves in the wet.
	weather = str(sim.get("weather")) if sim.get("weather") != null else ""
	weather = VignetteGrade.weather_of(weather)
	var wet := weather == "wet"
	_board = board_of(sim, my_side, shown)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%s|%d" % [str((sim.squads[0] as Squad).code), sim.current_minute])
	for side in range(2):
		var code := str((sim.squads[side] as Squad).code)
		_colours[side] = GameDB.club_colours(code)
		_codes[side] = code
		# MatchSim's own bounce: the ruck who goes up (a ruckman resting from the
		# ruck spot still goes up; a midfielder standing in it does not) and the
		# inside mids who attend. The scene never picks its own.
		var at: Dictionary = sim.bounce_attendees(side)
		var ruck: Dictionary = at["ruck"]
		var mids: Array = at["mids"]
		var picks := {"R": [] if ruck.is_empty() else [ruck],
				"C": mids.slice(0, 1), "RR": mids.slice(1, 2), "RV": mids.slice(2, 3)}
		var mine := side == my_side
		# Your side attacks up the screen, away from the camera; theirs faces it.
		var sgn := 1.0 if mine else -1.0
		for slot in SLOTS:
			for p in picks[slot]:
				var home: Vector2 = MatchDirector.CENTRE[slot]
				# World: x across the ground, y towards your goal.
				var to := Vector2(home.y, home.x) * sgn
				if slot == "R":
					to = Vector2(-0.9 * sgn, -7.0 * sgn)    # backed off for the run at it
				var from := to + Vector2(rng.randf_range(-9.0, 9.0), -sgn * rng.randf_range(14.0, 20.0))
				var tired := float(sim.energy.get(str(p["id"]), 100.0)) < EMPTY
				tokens.append({"side": side, "mine": mine, "slot": slot, "id": str(p["id"]),
						"tall": MatchSim._is_ruckman(p), "look": GameDB.figure_look(p, wet),
						"height_cm": float(p.get("height_cm", 0.0)),
						"name": _surname(GameDB.player_display_name(p)), "num": int(p["num"]),
						"tired": tired, "from": from, "to": to,
						"delay": rng.randf_range(0.0, 0.45),
						"dur": rng.randf_range(1.3, 1.7) * (1.6 if tired else 1.0)})
	_style_rucks()
	facts = _commentary(sim, my_side)
	# Everyone else: the wings, both arcs and the other umpires (the square is the bounce's own).
	_cast = VignetteExtras.players(sim, my_side, tokens.map(func(t): return str(t["id"])), Vector2.ZERO, wet, true) \
			+ VignetteExtras.umpires(Vector2.ZERO, Vector2.INF)
	_place_cast()
	_t = 0.0
	_hold = 0.0
	_idle = 0.0
	_frozen = false
	_shot.clear()
	_dress()
	if _ui == self:
		_ui = VignetteGrade.attach(self, weather, _draw_ui)
	queue_redraw()


## Where the names and bars draw: this node until setup, then the overlay above the
## grade (VignetteGrade) so text stays ungraded.
var _ui: CanvasItem = self


## The names, the bars and the cut-in fade.
func _draw_ui() -> void:
	var fade := clampf(_t / CUT_IN, 0.0, 1.0) if not _frozen else 1.0
	if _frozen:
		_draw_names()
	_draw_bars(fade)
	if fade < 1.0:
		_ui.draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 1.0 - fade), true)


## The two ruckmen contest differently, so they never go up as twins: one taps
## with an open hand, running straight at it; the other goes body-on, punching
## with the other fist, a beat later, lower, and from wider. Which is which
## follows the players (stable), not the side.
const RUCK_STYLES := [
	{"anim": "tap", "delay": 0.0, "peak": 1.1, "approach": -0.6},
	{"anim": "tap_b", "delay": 0.07, "peak": 0.85, "approach": 0.4},
]

func _style_rucks() -> void:
	var rucks := tokens.filter(func(t): return str(t["slot"]) == "R")
	rucks.sort_custom(func(a, b): return hash(str(a["id"])) < hash(str(b["id"])))
	for i in range(rucks.size()):
		(rucks[i] as Dictionary)["ruck"] = RUCK_STYLES[i % RUCK_STYLES.size()]


## The figure material, with both clubs' guernseys and the umpire's. Everything
## this Control draws goes through it; only the figures are recoloured.
func _dress() -> void:
	var kits := []
	for side in range(2):
		var code := str(_codes[side])
		var cols: Array = _colours[side]
		var trim: Color = cols[1] if cols.size() > 1 else Color.DIM_GRAY
		var kit: Dictionary = GameDB.club_guernsey(code) if code != "" else {
				"design": "plain", "base": cols[0] if cols.size() > 0 else Color.WHITE,
				"pattern": trim, "pattern2": Color.WHITE, "shorts": trim.darkened(0.1)}
		kits.append(kit)
	_kits = kits
	material = figure_material(kits + [UMPIRE_GEAR], material as ShaderMaterial)


## The umpire has no player behind him: one fixed look.
const UMPIRE_LOOK := {"skin": 1, "hair": 1}


static func _eight(palette: Array) -> Array:
	var out := palette.duplicate()
	while out.size() < 8:
		out.append(palette[palette.size() - 1])
	return out


## The umpire's kit, in the figures' palette.
const UMPIRE_GEAR := {"design": "plain", "base": UMPIRE, "pattern": Color(0.42, 0.62, 0.05),
		"pattern2": Color(0.42, 0.62, 0.05), "shorts": Color(0.1, 0.1, 0.12)}


## A material that recolours the figure sheet: up to four kits ({design, base,
## pattern, pattern2, shorts}, and optionally sock_hoops 0-3), addressed by index in a
## figure's draw colour.
## Reuses mat when given.
static func figure_material(kits: Array, mat: ShaderMaterial = null) -> ShaderMaterial:
	if mat == null or mat.shader != FIGURE_SHADER:
		mat = ShaderMaterial.new()
		mat.shader = FIGURE_SHADER
		mat.set_shader_parameter("mask_tex", FIGURE_MASK)
		mat.set_shader_parameter("design_tex", FIGURE_DESIGN)
		mat.set_shader_parameter("digits_tex", FIGURE_DIGITS)
		mat.set_shader_parameter("sheet_size", VignetteFigures.SHEET_SIZE)
		mat.set_shader_parameter("skin_tones", _eight(Appearance.SKIN))
		mat.set_shader_parameter("hair_tones", _eight(Appearance.HAIR))
		# The hair overlays' atlases, recognised by size as the figure sheet is.
		var sizes := []
		for tex in VignetteFigures.HAIR_TEXTURES + VignetteLooks.LOOK_TEXTURES:
			sizes.append(Vector2i((tex as Texture2D).get_size()))
		mat.set_shader_parameter("hair_count", sizes.size())
		while sizes.size() < 32:
			sizes.append(Vector2i(-1, -1))
		mat.set_shader_parameter("hair_sizes", sizes)
	var fields := {"base": [], "pattern": [], "pattern2": [], "shorts": [], "design": [], "extra": []}
	for i in range(4):
		var kit: Dictionary = kits[mini(i, kits.size() - 1)]
		for f in ["base", "pattern", "pattern2", "shorts"]:
			fields[f].append(kit[f])
		fields["design"].append(float(maxi(0, GameDB.GUERNSEY_DESIGNS.find(str(kit["design"])))))
		# Hoops on the socks, a kit option (0: the usual band).
		fields["extra"].append(Vector4(0.0, float(clampi(int(kit.get("sock_hoops", 0)), 0, 3)), 0.0, 0.0))
	for f in fields:
		mat.set_shader_parameter("kit_" + f, fields[f])
	return mat


## Straight to the frozen contest (a tap skips the play-in; tests).
func finish_now() -> void:
	_t = FREEZE
	_freeze()


func is_frozen() -> bool:
	return _frozen


func _process(delta: float) -> void:
	if _frozen:
		_after_freeze(delta)
		return
	_t += delta
	if _t >= FREEZE:
		_t = FREEZE
		_freeze()
	queue_redraw()


## After the freeze: the last push-in, then (a scene that idles) the clock the standing men,
## the crowd and the weather keep moving on while the coach decides. Settings > Reduced
## motion holds the frame still.
func _after_freeze(delta: float) -> void:
	if _hold < 0.4:
		_hold += delta
		queue_redraw()
	elif _idles() and not _reduced():
		_idle += delta
		# The men shift their weight three times a second: twelve pictures a second is plenty.
		if _idle - _idle_drawn >= 1.0 / 12.0:
			_idle_drawn = _idle
			queue_redraw()


## Whether the men, the crowd and the weather keep moving after the freeze. Not the centre
## bounce: its freeze is the top of the ruck contest, both men and the ball in the air, and
## nothing moves round a ball that hangs.
func _idles() -> bool:
	return false


func _reduced() -> bool:
	var gs := get_node_or_null("/root/GameState")
	return gs != null and gs.has_method("reduced_motion") and bool(gs.reduced_motion())


## The scene's clock: the play-in, then the time spent waiting on the call.
func clock() -> float:
	return _t + _idle


## When the scene freezes for the call, seconds in.
func _freeze_at() -> float:
	return FREEZE


func _freeze() -> void:
	if _frozen:
		return
	_frozen = true
	queue_redraw()
	ready_for_call.emit()


func _gui_input(event: InputEvent) -> void:
	if not _frozen and (event is InputEventMouseButton or event is InputEventScreenTouch) and event.is_pressed():
		finish_now()


# ---------------------------------------------------------------------------
# What the commentator says over the freeze: the story of the stoppages so
# far, in words. MatchSim's own counts decide it; none are shown.
# ---------------------------------------------------------------------------
func _commentary(sim: MatchSim, me: int) -> Array:
	return call_facts(sim, me)


## The same lines without the scene (Settings > Vignettes off): the call card
## carries them itself. MatchSim's bounce attendees, read the way setup() does.
static func call_facts(sim: MatchSim, me: int) -> Array:
	var at_bounce := []
	for side in range(2):
		var at: Dictionary = sim.bounce_attendees(side)
		var ruck: Dictionary = at["ruck"]
		var mids: Array = at["mids"]
		var picks := {"R": [] if ruck.is_empty() else [ruck],
				"C": mids.slice(0, 1), "RR": mids.slice(1, 2), "RV": mids.slice(2, 3)}
		for slot in SLOTS:
			for p in picks[slot]:
				at_bounce.append({"mine": side == me, "slot": slot,
						"name": _surname(GameDB.player_display_name(p)),
						"tired": float(sim.energy.get(str(p["id"]), 100.0)) < EMPTY})
	var out := []
	var them := 1 - me
	var gap := float((sim.team_stats[me] as Dictionary).get("clearances", 0.0)) \
			- float((sim.team_stats[them] as Dictionary).get("clearances", 0.0))
	var taps := _ruck_taps(sim, me) - _ruck_taps(sim, them)
	var rucks := {}
	for t in at_bounce:
		if str(t["slot"]) == "R":
			rucks[bool(t["mine"])] = str(t["name"])
	if gap <= -4:
		out.append("They have been winning it out of the middle all day.")
	elif gap >= 4:
		out.append("You have had the better of them out of the middle all day.")
	elif absi(taps) >= 5 and rucks.has(taps > 0):
		out.append("%s is on top in the ruck." % str(rucks[taps > 0]))
	else:
		out.append("Nothing between them at the stoppages.")
	for t in at_bounce:
		if bool(t["tired"]):
			out.append(("%s is running on empty." if bool(t["mine"]) else "Their %s is running on empty.")
					% str(t["name"]))
			break
	return out


static func _ruck_taps(sim: MatchSim, side: int) -> int:
	var n := 0.0
	for p in (sim.squads[side] as Squad).ground:
		if str(p["role"]) == "RUCK":
			n += _stat(sim, p, "hitouts")
	return int(n)


static func _stat(sim: MatchSim, p: Dictionary, key: String) -> float:
	return float((sim.player_stats.get(str(p["id"]), {}) as Dictionary).get(key, 0.0))


static func _surname(full: String) -> String:
	var parts := full.split(" ")
	return parts[parts.size() - 1] if parts.size() > 0 else full


# ---------------------------------------------------------------------------
# The camera: a broadcast camera behind your end, low and on a long lens, so the stand and
# the crowd fill the top of the picture and the turf is a strip under the men's boots. It
# opens wider on the square while the set-up builds (both rucks, the mids, the umpire), then
# zooms in on the contest as the ball goes up. It stays where it is: only the lens moves, so
# the picture scales as one and nothing changes shape (it used to travel in from 34 m to
# 18 m, and the square and the players warped as it came - director).
#
# Where it stands is worked out from the picture wanted at the freeze, never guessed
# (director, 2026-11-09 and the 2026-11-12 visual interview): the men a given size, the turf
# from the far fence to the bottom of the picture no more than a third of it, the top of the
# stand just under the title bar (_solve).
# ---------------------------------------------------------------------------
## At the settled freeze, as shares of the open picture (under the title bar, above the call):
## the turf from the far fence's foot down to the bottom, and the gap left under the boots.
const GRASS_SHARE := 0.32
const FEET_SHARE := 0.07
## How much of the screen the call takes when it is up, for working out the turf's share
## before the call exists: a tall phone's and a wide window's.
const CALL_SHARE := [0.4, 0.3]
## The top of the stand sits this far under the title bar: a strip of sky for the towers.
const STAND_TOP := 0.04
## The contest stays this far under the title bar, pixels.
const HEAD_ROOM := 30.0
var _cam_d := 46.0
var _cam_h := 12.0
var _focal := 400.0
var _horizon := 0.0
var _cam_x := CAM_X
var _zoom := 1.0                  # how far the lens has zoomed since the start
var _pan := 0.0                   # pixels the camera has turned across, at this zoom
## The camera worked out for this screen (_solve); empty until first asked for.
var _shot := {}
var _idle := 0.0                  # seconds waited on the call since the freeze settled
var _idle_drawn := 0.0
## Everyone else on the ground (VignetteExtras): drawn with the scene's men, never in tokens.
var _cast: Array = []


## What the freeze frames, in the scene's metres: "near" how far up the scene the nearest
## boots are and "mid" where across it the picture centres; "half" how far the men spread
## either side of that; "top" the top of the action above the turf (the figures' larger-than-
## life metres); "tall" how much of the open picture that may stand; "d" the lens's distance
## from the near boots (0: found, so the stand fills the top); "x" how far across the camera
## stands; "feet" the gap under the boots (a share, FEET_SHARE by default).
func _subject() -> Dictionary:
	# The ruck contest: both ruckmen up, the ball above them, the first midfielders either side.
	# (The first midfielders stand five metres either side of the circle: both in the picture.)
	return {"near": -1.5, "mid": 0.0, "half": 5.7, "top": 6.0, "tall": 0.55, "d": 0.0,
			"x": CAM_X, "feet": 0.1}


## The camera for this screen: worked out once per size.
func shot() -> Dictionary:
	if _shot.is_empty() or (_shot["size"] as Vector2) != size:
		_shot = _solve()
		_clear_posts()
	return _shot


## Whether an oval spot is inside the boundary line pushed out by margin metres.
static func _inside(p: Vector2, margin: float) -> bool:
	return pow(p.x / (VignetteGround.A + margin), 2.0) + pow(p.y / (VignetteGround.L + margin), 2.0) < 1.0


## Where the camera stands and how long its lens is, from the picture wanted at the freeze.
## A level lens draws a point h metres up and z metres away at horizon + f * (H - h) / z, so:
##   s, pixels per metre at the near boots: the top of the action "tall" of the open picture,
##      or the men's spread across 92% of the width, whichever is smaller;
##   H, the camera's height: the turf between the near boots and the far fence's foot is
##      s * H * Db / (d + Db) pixels tall (Db: boots to fence), set to the turf's share;
##   d, its distance: the top of the stand (Hs up, Ds away) is drawn at
##      boots - s * H + s * d * (H - Hs) / (d + Ds); the camera backs off, the lens growing
##      with it, until that reaches the title bar - or the camera reaches the fence behind it.
func _solve() -> Dictionary:
	if VignetteGround.spec.is_empty():
		VignetteGround.venue = VignetteGround.venue
	var sub := _subject()
	var bar := size.y * 0.075
	var open := maxf(40.0, size.y - 2.0 * bar)
	var feet_share := float(sub.get("feet", FEET_SHARE))
	var s := minf(float(sub["tall"]) * open / float(sub["top"]), 0.92 * size.x / (2.0 * float(sub["half"])))
	var feet := size.y - bar - feet_share * open
	# The turf's strip is sized for the picture left above the call, so the share holds there.
	var open_call := maxf(40.0, size.y * (1.0 - float(CALL_SHARE[1 if size.x > size.y else 0])) - bar)
	var strip := (GRASS_SHARE - feet_share) * open_call
	var back := _ground_to_scene().affine_inverse()
	var here := Vector2(float(sub["mid"]), float(sub["near"]))
	var db := 1.0
	while db < 400.0 and _inside(back * (here + Vector2(0.0, db)), VignetteGround.FENCE):
		db += 0.5
	var tiers: Array = VignetteGround.spec["tiers"]
	var upper: Array = tiers[tiers.size() - 1]
	var ds := db + 2.0 + float(upper[1])
	var hs := float(upper[3])
	var want := bar + STAND_TOP * open
	var x := float(sub["x"])
	var d := float(sub["d"])
	if d <= 0.0:
		d = 9.0
		while d < 120.0:
			var h_try := strip * (d + db) / (s * db)
			if feet - s * h_try + s * d * (h_try - hs) / (d + ds) <= want:
				break
			# The camera stays on the ground: never behind a goal line, its posts in front of it.
			if not _inside(back * Vector2(x, float(sub["near"]) - d - 1.0), -1.0):
				break
			d += 0.5
	var h := strip * (d + db) / (s * db)
	return {"size": size, "bar": bar, "open": open, "s": s, "d": d, "h": h, "x": x, "feet": feet,
			"feet_share": feet_share, "near": float(sub["near"]), "mid": float(sub["mid"]),
			"top": float(sub["top"]), "db": db, "ds": ds, "hs": hs}


## The call's room as the camera uses it: never more than six tenths of the picture (the
## match screen has handed over a panel's height before the panel was laid out).
func _room() -> float:
	return minf(call_room, size.y * 0.6)


## At the settled freeze: how far the lens eases out so the top of the action stays under
## the title bar (x; 1 when it fits), and where the near boots sit above the call (y).
func _freeze_fit() -> Vector2:
	var bar: float = _shot["bar"]
	var floor_y := size.y - maxf(_room(), bar)
	var feet := floor_y - float(_shot["feet_share"]) * (floor_y - bar)
	return Vector2(clampf((feet - bar - HEAD_ROOM) / (float(_shot["top"]) * float(_shot["s"])), 0.4, 1.0), feet)


func _set_camera() -> void:
	shot()
	_apply_camera(_t, _hold)


## The camera at t seconds into the play-in and hold seconds into the freeze's last move.
func _apply_camera(t: float, hold_t: float) -> void:
	# The wider shot holds (a slow creep keeps it alive), then the push-in eases in and out.
	var hold := clampf(t / PUSH_IN, 0.0, 1.0)
	var k := _smooth(clampf((t - PUSH_IN) / (FREEZE - PUSH_IN), 0.0, 1.0))
	var punch := _ease(clampf(hold_t / 0.4, 0.0, 1.0))
	var d: float = _shot["d"]
	var s: float = _shot["s"]
	var fit := _freeze_fit()
	# Wide enough for the whole square's set-up (eight metres either side) where the screen
	# has the width; a phone's stays closer, or the men are specks under an empty sky.
	var wide := clampf(0.92 * size.x / (16.0 * s), 0.74, 0.9)
	var z: float = lerpf(lerpf(lerpf(wide, wide * 1.04, hold), 0.95, k), fit.x, punch)
	_cam_d = d - float(_shot["near"])
	_cam_h = _shot["h"]
	_cam_x = _shot["x"]
	_focal = s * d * z
	_zoom = z / wide
	# The wide shot is turned onto the centre of the square, so the set-up sits in the middle
	# of the picture; then it pans across with the ruckmen to the contest. A pan turns the
	# camera on its head, which moves the whole picture as one; the camera itself stays
	# where it is (sliding it across would move the near turf more than the far, and the
	# painted lines would skew as it went - director).
	_pan = _focal * (lerpf(0.0, float(_shot["mid"]), k) - _cam_x) / d
	# The near boots sit at the bottom of the picture while the play builds, then lift clear
	# of the call as it slides up - a tilt, the same move as the last push.
	_horizon = lerpf(float(_shot["feet"]), fit.y, punch) - _focal * _cam_h / d


## The men whose names show at the freeze: the rucks, the first midfielder each side and
## anyone out on their feet. Not a roll call.
func _named() -> Array:
	return tokens.filter(func(t): return str(t["slot"]) in ["R", "C"] or bool(t["tired"]))


## How far across the camera may step, in metres from where the scene put it, to get a goal
## post out from behind a named man: nearest first.
func _cam_steps() -> Array:
	var out := [0.0]
	for i in range(1, 17):
		out.append(0.5 * i)
		out.append(-0.5 * i)
	return out


## No goal or behind post rises out of a named man's head at the freeze: the camera steps
## across until every post that tops a man stands clear of his shoulders.
func _clear_posts() -> void:
	var keep := Vector2(_t, _hold)
	var base: float = _shot["x"]
	_t = _freeze_at()
	_hold = 0.4
	for step in _cam_steps():
		_shot["x"] = base + float(step)
		_apply_camera(_t, _hold)
		if _shot_good():
			break
		_shot["x"] = base
	_t = keep.x
	_hold = keep.y
	_apply_camera(_t, _hold)


## Whether the camera, stepped across to here, gives a picture this scene accepts.
func _shot_good() -> bool:
	return posts_clear()


## Whether every post that rises above a named man's head stands clear of his shoulders,
## with the camera and the men as they are now.
func posts_clear() -> bool:
	var cam := ground_cam()
	for end in [-1.0, 1.0]:
		for i in [-1.5, -0.5, 0.5, 1.5]:
			var at := Vector2(i * VignetteGround.GOAL_GAP, VignetteGround.GOAL_Y * end)
			var foot := cam.oval(at)
			if foot.z <= 0.0:
				continue
			var tip := cam.oval(at, VignetteGround.GOAL_H if absf(i) < 1.0 else VignetteGround.BEHIND_H)
			for t in _named():
				var p := _pos(t)
				var feet := _project(p, _lift(t))
				var head := _project(p, _lift(t) + _head_top(t))
				if foot.z >= feet.z or tip.y >= head.y:
					continue          # nearer than he is, or it stops below the top of his head
				# (The post itself, a hand's width, and a gap: its pad stops well below his head.)
				if absf(foot.x - feet.x) < SHOULDER * FIGURE * feet.z + maxf(1.5, 0.2 * foot.z):
					return false
	return true


## Half a man's width across the shoulders and arms, metres (before FIGURE).
const SHOULDER := 0.42


## The freeze's picture in numbers, for the tests and the capture tools: where the camera
## stands and, down the screen, the title bar, the top of the stand, the far fence's foot
## (where the turf starts), the named men's heads and boots and the bottom of the open
## picture; and the turf's share of the whole frame and of the open picture.
func shot_numbers() -> Dictionary:
	shot()
	var keep := Vector2(_t, _hold)
	_t = _freeze_at()
	_hold = 0.4
	_apply_camera(_t, _hold)
	var bar: float = _shot["bar"]
	var floor_y := size.y - maxf(_room(), bar)
	var here := Vector2(float(_shot["mid"]), float(_shot["near"]))
	var fence := _project(here + Vector2(0.0, float(_shot["db"])))
	var stand := _project(here + Vector2(0.0, float(_shot["ds"])), float(_shot["hs"]))
	var head := INF
	var feet := -INF
	var tallest := 0.0
	var men := _named()
	for t in men if not men.is_empty() else tokens:
		var p := _pos(t)
		var top := _project(p, _lift(t) + _head_top(t)).y
		var boots := _project(p, _lift(t)).y
		head = minf(head, top)
		feet = maxf(feet, _project(p).y)
		tallest = maxf(tallest, boots - top)
	var out := {"size": size, "cam_d": float(_shot["d"]), "cam_h": _cam_h, "cam_x": _cam_x,
			"px_per_m": _focal / float(_shot["d"]), "bar": bar, "stand_top": stand.y, "horizon": _horizon,
			"grass_top": fence.y, "head": head, "feet": feet, "floor": floor_y, "man_px": tallest,
			"grass_of_frame": (floor_y - fence.y) / size.y,
			"grass_of_open": (floor_y - fence.y) / maxf(1.0, floor_y - bar),
			"stand_of_open": (fence.y - maxf(bar, stand.y)) / maxf(1.0, floor_y - bar)}
	_t = keep.x
	_hold = keep.y
	_apply_camera(_t, _hold)
	return out


## Stands the cast in the scene (oval metres to the scene's), leaving out anyone who would
## stand on one of the scene's own men or in his path, or nearer the camera than they are.
func _place_cast() -> void:
	var to_scene := _ground_to_scene()
	var nearest := INF
	for t in tokens:
		nearest = minf(nearest, minf((t["to"] as Vector2).y, (t["from"] as Vector2).y))
	var kept := []
	for e in _cast:
		var at: Vector2 = to_scene * (e["oval"] as Vector2)
		if at.y < nearest + 1.0 or not _cast_fits(at):
			continue
		if tokens.any(func(t): return Geometry2D.get_closest_point_to_segment(at, t["from"], t["to"]).distance_to(at) < 3.0):
			continue
		e["at"] = at
		kept.append(e)
	_cast = kept


## Whether one of the cast may stand at that spot of the scene (a scene keeps its own
## ground clear).
func _cast_fits(at: Vector2) -> bool:
	# The centre square is the bounce's: four a side, no more.
	return absf(at.x) > 26.0 or absf(at.y) > 26.0


## What the cast watch: the ball.
func _cast_focus() -> Vector2:
	var b := _ball()
	return Vector2(b.x, b.y)


## World (x across, y towards your goal, h up) to screen, and metres to pixels there.
func _project(p: Vector2, h := 0.0) -> Vector3:
	var z := maxf(0.5, p.y + _cam_d)
	return Vector3(size.x * 0.5 - _pan + _focal * (p.x - _cam_x) / z, _horizon + _focal * (_cam_h - h) / z, _focal / z)


static func _ease(k: float) -> float:
	return 1.0 - pow(1.0 - k, 3.0)


## Eased in and out: a lens move that starts and lands softly.
static func _smooth(k: float) -> float:
	return k * k * (3.0 - 2.0 * k)


# ---------------------------------------------------------------------------
# The scene, beat by beat.
# ---------------------------------------------------------------------------
func _pos(t: Dictionary) -> Vector2:
	var k := clampf((_t - float(t["delay"])) / float(t["dur"]), 0.0, 1.0)
	var p := (t["from"] as Vector2).lerp(t["to"], _ease(k))
	var sgn := 1.0 if bool(t["mine"]) else -1.0
	if str(t["slot"]) == "R":
		var style: Dictionary = t.get("ruck", RUCK_STYLES[0])
		var run := clampf((_t - RUN_IN[0] - float(style["delay"])) / (RUN_IN[1] - RUN_IN[0]), 0.0, 1.0)
		p = p.lerp(Vector2(float(style["approach"]) * sgn, -1.0 * sgn), run * run)
	elif k >= 1.0:
		# Settled in the square: jostling for the front spot.
		p.x += sin(_t * 3.1 + float(t["num"])) * 0.35
	return p


func _moving(t: Dictionary) -> bool:
	if str(t["slot"]) == "R" and _t >= RUN_IN[0] and _t < RUN_IN[1]:
		return true
	var k := (_t - float(t["delay"])) / float(t["dur"])
	return k > 0.0 and k < 0.95


func _lift(t: Dictionary) -> float:
	if str(t["slot"]) != "R":
		return 0.0
	var style: Dictionary = t.get("ruck", RUCK_STYLES[0])
	var start := RUN_IN[1] - 0.1 + float(style["delay"])
	if _t < start:
		return 0.0
	return float(style["peak"]) * _ease(clampf((_t - start) / 0.35, 0.0, 1.0))


func _umpire() -> Vector2:
	var k := clampf((_t - UMP_IN[0]) / (UMP_IN[1] - UMP_IN[0]), 0.0, 1.0)
	var at := Vector2(11.0, 3.0).lerp(Vector2(1.2, 0.4), _ease(k))
	# Out of the way once it is bounced.
	return at.lerp(Vector2(4.5, 2.5), _ease(clampf((_t - BALL_UP) / 0.6, 0.0, 1.0)))


func _ball() -> Vector3:
	# x, y on the ground and height: in the umpire's hand, raised, down, then up.
	var u := Vector2(1.2, 0.4) if _t >= BALL_UP else _umpire()
	if _t < BALL_UP - 0.5:
		return Vector3(u.x - 0.4, u.y, 1.1)
	if _t < BALL_UP - 0.15:
		return Vector3(u.x - 0.4, u.y, lerpf(1.1, 2.1, (_t - (BALL_UP - 0.5)) / 0.35))
	if _t < BALL_UP:
		var k := (_t - (BALL_UP - 0.15)) / 0.15
		return Vector3(lerpf(u.x - 0.4, 0.0, k), lerpf(u.y, 0.0, k), lerpf(2.1, 0.0, k))
	var up := _ease(clampf((_t - BALL_UP) / (FREEZE - BALL_UP), 0.0, 1.0))
	return Vector3(0.0, 0.0, 5.5 * up)


func _draw() -> void:
	_set_camera()
	_draw_ground()
	var lights := VignetteAtmos.draw_back(self, ground_cam(), Rect2(Vector2.ZERO, size), weather)
	# Far to near, so the nearer players stand in front.
	var figures := []
	for t in tokens:
		figures.append({"at": _pos(t), "t": t})
	for e in _cast:
		figures.append({"at": e["at"], "t": e})
	figures.append({"at": _umpire(), "t": {}})
	figures.sort_custom(func(a, b): return (a["at"] as Vector2).y > (b["at"] as Vector2).y)
	var b := _ball()
	var ball_drawn := false
	for f in figures:
		if not ball_drawn and (f["at"] as Vector2).y < b.y:
			_draw_ball(b)
			ball_drawn = true
		_draw_figure(f["at"], f["t"])
	if not ball_drawn:
		_draw_ball(b)
	VignetteWeather.draw_air(self, Rect2(Vector2.ZERO, size), clock(), weather)
	VignetteAtmos.draw_front(self, Rect2(Vector2.ZERO, size), lights, weather, clock())
	if _frozen:
		# The freeze: a flash on the cut, then the frame held a shade darker.
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.18), true)
		if _hold < 0.15:
			draw_rect(Rect2(Vector2.ZERO, size), Color(1, 1, 1, 0.5 * (1.0 - _hold / 0.15)), true)
	if _ui == self:
		_draw_ui()


## The ground (VignetteGround, to the AFL's dimensions) through this scene's camera: the
## stands and the crowd, the fence, the boundary, the centre square and circles, the arcs
## and the far goals - all seen in perspective, so they hold their shape as it zooms.
func _draw_ground() -> void:
	var cam := ground_cam()
	# The same crowd as the replay's (seed CROWD), so the stadium is one place all match.
	VignetteGround.draw_ground(self, cam, Rect2(Vector2.ZERO, size), _colours, CROWD, _screen_board(cam), weather, clock())
	VignetteCrowd.stir(self, cam, _colours, clock(), CROWD)
	VignetteGround.draw_goals(self, cam, 1, _pad_colour())
	VignetteGround.draw_goals(self, cam, -1, _pad_colour())


## The crowd every match scene seats (BroadcastVignette draws the replay with the same).
const CROWD := 11


## The score for the big screen through this camera; a scene can leave the screen out.
func _screen_board(_cam: VignetteGround.Cam) -> Dictionary:
	return _board


## This scene's camera, as the ground sees it.
func ground_cam() -> VignetteGround.Cam:
	var cam := VignetteGround.Cam.new()
	cam.pos = Vector2(_cam_x, -_cam_d)
	cam.height = _cam_h
	cam.f = _focal
	cam.cx = size.x * 0.5 - _pan
	cam.hor = _horizon
	cam.to_scene = _ground_to_scene()
	return cam


## Where the scene stands on the ground: oval coordinates to the scene's. The centre
## bounce is at the centre of the ground, the length running away from the camera.
func _ground_to_scene() -> Transform2D:
	return Transform2D.IDENTITY


## The padding round the goal posts: the home club's colour.
func _pad_colour() -> Color:
	var c: Array = _colours[0] if not _colours.is_empty() else []
	return (c[0] as Color) if not c.is_empty() else Color(0.7, 0.7, 0.72)


func _draw_figure(at: Vector2, t: Dictionary) -> void:
	if at.y + _cam_d < 1.2:
		return               # beside or behind the camera
	var ump := t.is_empty() or t.has("ump")
	var lift := 0.0 if ump or t.has("extra") else _lift(t)
	var base := _project(at, lift)
	var ground := _project(at)
	var m := base.z * FIGURE           # pixels per (larger than life) metre
	if base.x < -1.5 * m or base.x > size.x + 1.5 * m:
		return               # off the side of the picture
	var tired := not ump and bool(t.get("tired", false))
	# Your players have their backs to us; theirs and the umpire face the camera.
	var back := not ump and bool(t.get("mine", false))
	var pick := _frame(t, lift, at, back)
	# A move can name its own side (a fourth entry: the kick is only drawn from behind,
	# three-quarters on).
	var facing: String = str(pick[3]) if pick.size() > 3 else ("back" if back else "front")
	var build := _body(t)
	if not VignetteFigures.has(build, pick[0], facing):
		build = "average"
	var info := VignetteFigures.strip(build, pick[0], facing)
	var frame := figure_frame(info, int(pick[1]), pick[0], facing)
	var src := VignetteFigures.source(info, frame)
	# Out on their feet: a touch smaller, stooped.
	var k := m / VignetteFigures.PX_PER_M * (0.96 if tired else 1.0)
	var mirror := bool(pick[2])
	# Shadow on the ground under his boots (the strip's contact), smaller as he leaves it.
	var under := VignetteFigures.contact(info) * k
	if mirror:
		under.x = -under.x
	var sh := 0.38 * m * (1.0 - lift * 0.35) * VignetteWeather.shadow_tight(weather)
	draw_set_transform(Vector2(ground.x, ground.y) + under, 0.0, Vector2(1.0, 0.32))
	draw_circle(Vector2.ZERO, sh, Color(0, 0, 0, VignetteWeather.shadow_alpha(weather) + 0.03))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	var kit := UMPIRE_KIT if ump else int(t["side"])
	var look: Dictionary = t.get("look", UMPIRE_LOOK)
	draw_frame(self, Vector2(base.x, base.y), info, frame, k, look_colour(kit, look, mirror), mirror,
			number_colour(kit, int(t.get("num", 0)), 1.0, mirror) if facing.begins_with("back") and m > 18.0 else Color(0, 0, 0, 0),
			Transform2D.IDENTITY, str(look.get("hair_style", VignetteFigures.HAIR_BASE)), face_of(look),
			ink_of(look))


## Draws frame f of a strip with its feet at feet, k screen pixels per frame pixel,
## on ci (whose material must be the figure material). Mirrored, it faces the other
## way: flipped about the feet by a draw transform (a negative-size rect isn't drawn).
## number: a second pass that prints the number (number_colour), or alpha 0 for none.
## view: the vignette's camera (VignetteCamera) that ci is drawing through.
## hair_style: his hair (Appearance.HAIR_STYLES), drawn over the bald figure
## straight after it (VignetteFigures.hair_for: a style with no art yet draws
## the base look), so a man in front still covers the hair of one behind.
## face: his brows (face_of), or -1 for no face.
## ink: his premiership years on the bicep (figure_look "flag_ink"; 0 for none):
## drawn on the figure before his hair, in its own colour (VignetteInk).
static func draw_frame(ci: CanvasItem, feet: Vector2, info: Dictionary, f: int, k: float, colour: Color,
		mirror := false, number := Color(0, 0, 0, 0), view := Transform2D.IDENTITY,
		hair_style := VignetteFigures.HAIR_BASE, face := -1, ink := 0) -> void:
	var pivot := Vector2(info["pivot"][0], info["pivot"][1])
	var dest := Rect2(feet - pivot * k, VignetteFigures.frame_size(info) * k)
	var src := VignetteFigures.source(info, f)
	if mirror:
		ci.draw_set_transform_matrix(view * Transform2D(0.0, Vector2(-1.0, 1.0), 0.0, Vector2(2.0 * feet.x, 0.0)))
	ci.draw_texture_rect_region(FIGURE_SHADE, dest, src, colour)
	if number.a > 0.0:
		ci.draw_texture_rect_region(FIGURE_SHADE, dest, src, number)
	var ic := VignetteInk.cell(info, ink)
	if not ic.is_empty():
		if log_frames:
			ink_log.append({"years": ink, "texture": VignetteInk.texture(ic)})
		_draw_look(ci, dest.position, ic, f, k, Color(1, 1, 1, colour.a), VignetteInk.texture(ic))
	draw_hair(ci, dest.position, info, f, k, colour, hair_style, face)
	if mirror:
		ci.draw_set_transform_matrix(view)


## A figure's hair overlay: frame f of its style's hair strip over the figure drawn
## at origin (its dest rect's top-left), in his hair colour (or his skin, for a bare
## scalp: VignetteFigures.HAIR_TINT_SKIN). colour is the figure's look_colour.
## His face (face >= 0: VignetteLooks.FACES[face], eyes and brows) is drawn first, in his
## hair colour, and the styles in VignetteLooks.HAIR_STYLES draw their own hair.
static func draw_hair(ci: CanvasItem, origin: Vector2, info: Dictionary, f: int, k: float, colour: Color,
		hair_style: String, face := -1) -> void:
	if face >= 0 and face < VignetteLooks.FACES.size():
		var fc := VignetteLooks.cell(info, VignetteLooks.FACES[face])
		if log_frames and not fc.is_empty():
			face_log.append({"texture": VignetteLooks.texture(fc)})
		_draw_look(ci, origin, fc, f, k, Color(0.0, colour.g, colour.b, colour.a))
	if hair_style in VignetteLooks.HAIR_STYLES:
		var c := VignetteLooks.cell(info, hair_style)
		if not c.is_empty():
			if log_frames:
				hair_log.append({"style": hair_style, "texture": VignetteLooks.texture(c)})
			_draw_look(ci, origin, c, f, k, Color(0.0, colour.g, colour.b, colour.a))
			return
	var h := VignetteFigures.hair_for(info, hair_style)
	if h.is_empty():
		return
	if log_frames:
		hair_log.append({"style": hair_style, "texture": VignetteFigures.hair_texture(h)})
	var skin := 1.0 if hair_style in VignetteFigures.HAIR_TINT_SKIN else 0.0
	ci.draw_texture_rect_region(VignetteFigures.hair_texture(h),
			Rect2(origin + VignetteFigures.hair_offset(h) * k, Vector2(h["size"][0], h["size"][1]) * k),
			VignetteFigures.hair_source(h, f), Color(skin, colour.g, colour.b, colour.a))


## A VignetteLooks cell (VignetteLooks.cell) over the figure drawn at origin, or nothing.
static func _draw_look(ci: CanvasItem, origin: Vector2, c: Dictionary, f: int, k: float, colour: Color,
		tex: Texture2D = null) -> void:
	if c.is_empty():
		return
	ci.draw_texture_rect_region(tex if tex != null else VignetteLooks.texture(c),
			Rect2(origin + Vector2(c["offset"][0], c["offset"][1]) * k, Vector2(c["size"][0], c["size"][1]) * k),
			VignetteFigures.hair_source(c, f), colour)


## The premiership years a look draws on the bicep (draw_frame's ink; 0 for none).
static func ink_of(look: Dictionary) -> int:
	return int(look.get("flag_ink", 0))


## The face a look draws (draw_frame's face): his brows
## (Appearance.brows_for; 0 for a look without them, the umpire's).
static func face_of(look: Dictionary) -> int:
	return int(look.get("brows", 0))


## The draw colour that recolours a figure: its kit, whether he wears long sleeves,
## skin and hair, and whether the frame is mirrored (figure.gdshader).
static func look_colour(kit: int, look: Dictionary, mirror := false, alpha := 1.0) -> Color:
	return Color(kit_code(kit, bool(look.get("long_sleeves", false)), mirror), int(look["skin"]) / 8.0,
			int(look["hair"]) / 8.0, alpha)


## A draw colour's red: kit, long sleeves and mirrored, packed as the shader reads them.
static func kit_code(kit: int, sleeves: bool, mirror: bool) -> float:
	return (clampi(kit, 0, 3) * 4 + (2 if sleeves else 0) + (1 if mirror else 0)) / 16.0


## The draw colour that prints a number (0-99) on a figure's back instead of
## drawing the figure (figure.gdshader): draw the same frame again with it.
static func number_colour(kit: int, number: int, alpha := 1.0, mirror := false) -> Color:
	return Color(kit_code(kit, false, mirror), 1.0, (clampi(number, 0, 99) + 1) / 128.0, alpha)


## Ruckmen are the tall figures; small men (BroadcastVignette.SMALL_CM) the small
## build; everyone else - an emergency ruck from the midfield included, and the
## umpire - the average build.
static func _body(t: Dictionary) -> String:
	if bool(t.get("tall", false)):
		return "ruck"
	var cm := float(t.get("height_cm", 0.0))
	return "small" if cm > 0.0 and cm < BroadcastVignette.SMALL_CM else "average"


## Which animation and frame a figure shows now, and whether it's mirrored:
## [anim, frame, mirror]. at: where he stands; back: his back is to us.
func _frame(t: Dictionary, lift: float, at := Vector2.ZERO, back := false) -> Array:
	if t.is_empty():
		# The umpire walks in, raises the ball, bounces it and follows through.
		if _t >= BALL_UP - 0.5 and _t < BALL_UP - 0.15:
			return ["bounce", 1, false]
		if _t >= BALL_UP - 0.15 and _t < BALL_UP:
			return ["bounce", 2, false]
		if _t >= BALL_UP and _t < BALL_UP + 0.4:
			return ["bounce", 3, false]
		if _t >= UMP_IN[0] and _t < UMP_IN[1]:
			return ["jog", int(_t * 10.0) % 8, false]
		return _ready_pick({"num": 0, "id": "umpire"}, at, false)
	if t.has("extra"):
		return _cast_frame(t, at)
	if lift > 0.0:
		# The ruck contest, one-handed, each ruckman his own way (RUCK_STYLES).
		var style: Dictionary = t.get("ruck", RUCK_STYLES[0])
		var frames := 6 if str(style["anim"]) == "tap" else 4
		var k := clampf(lift / float(style["peak"]), 0.0, 1.0)
		return [style["anim"], int(roundf(k * (frames - 1))), false]
	if _moving(t):
		# Each man at his own stride; slower when they're out on their feet.
		var strides := (9.0 if bool(t["tired"]) else 13.0) / TAU * _rate(t, 0.9, 1.1)
		return ["jog", int(_t * strides * 8.0 + float(t["num"])) % 8, false]
	return _ready_pick(t, at, back)


## Standing, he's ready, not stiff: knees bent and bouncing at his own rate, his
## head and shoulders turned to what he's watching when it's off to one side
## (mirrored for his right). Two men side by side never move as one.
func _ready_pick(t: Dictionary, at: Vector2, back: bool) -> Array:
	return _watch_pick(t, at, back, _look_at(t))


## One of the cast: standing ready, watching the play, his back to us when it is beyond him.
func _cast_frame(t: Dictionary, at: Vector2) -> Array:
	var focus := _cast_focus()
	var back := focus.y > at.y + 1.0
	var pick := _watch_pick(t, at, back, focus)
	return [pick[0], pick[1], pick[2], "back" if back else "front"]


## _ready_pick, watching that spot of the scene. The scene's clock drives it, so a man goes
## on shifting his weight while the coach decides (a scene that idles).
func _watch_pick(t: Dictionary, at: Vector2, back: bool, target: Vector2) -> Array:
	var cycle := int(clock() * 3.0 * _rate(t, 0.7, 1.15) + float(t["num"]) * 0.37 + _rate(t, 0.0, 3.0)) % 3
	var to := target - at
	# Across his line of sight: his back to us, his left is the screen's left.
	var across := -to.x if back else to.x
	if absf(to.x) < 0.35 * absf(to.y) + 1.0:
		# Looking ahead, in one of two stances of his own (a third of men side-on and low,
		# arms out), mirrored on a whim so a row isn't a row of clones.
		var stance := "ready_b" if _rate(t, 0.0, 1.0) < 0.35 and VignetteFigures.has(_body(t), "ready_b", "back" if back else "front") \
				else "ready"
		return [stance, cycle, _rate(t, 0.0, 1.0) > 0.5 if stance == "ready" else _rate(t, 0.0, 1.0) < 0.17]
	return ["ready_turn", cycle, across < 0.0]


## What a standing man watches: the ball (the pre-match scene overrides it).
func _look_at(_t_: Dictionary) -> Vector2:
	var b := _ball()
	return Vector2(b.x, b.y)


## A number of his own between lo and hi, stable for the man.
static func _rate(t: Dictionary, lo: float, hi: float) -> float:
	var h := hash(str(t.get("id", t.get("num", 0))) + "|rate")
	return lo + (hi - lo) * float(absi(h) % 1000) / 999.0


## Height of a figure's head (or raised hands) above its feet, world metres.
func _figure_top(t: Dictionary) -> float:
	var tall := float(VignetteFigures.BODIES[_body(t)]["height_m"])
	return (tall + (0.75 if _lift(t) > 0.0 else 0.1)) * FIGURE


## Where the top of his head is drawn above his boots (his hands, when he is up with his
## arms raised), world metres: the sheets draw a man a little under his listed height, so a
## name pinned here sits on his head and a post is judged against the head we see.
func _head_top(t: Dictionary) -> float:
	var tall := float(VignetteFigures.BODIES[_body(t)]["height_m"])
	return (0.86 * tall + (0.36 if _lift(t) > 0.0 else 0.0) + 0.04) * FIGURE * (0.96 if bool(t.get("tired", false)) else 1.0)


func _draw_ball(b: Vector3) -> void:
	var g := _project(Vector2(b.x, b.y))
	var s := _project(Vector2(b.x, b.y), b.z)
	var r := maxf(3.0, 0.2 * s.z * FIGURE)
	draw_set_transform(Vector2(g.x, g.y), 0.0, Vector2(1.0, 0.35))
	draw_circle(Vector2.ZERO, r * (1.0 - clampf(b.z / 10.0, 0.0, 0.6)), Color(0, 0, 0, 0.3))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# The Sherrin (VignetteBall), spinning once it's up off the umpire's bounce.
	VignetteBall.draw(self, Vector2(s.x, s.y), 2.0 * r, _t, b.z > 0.6)


## At the freeze: who is who, for the rucks, the first midfielder each side and
## anyone out on their feet. Not a roll call.
func _draw_names() -> void:
	var keep := []
	# The ball is the point of the frame: no name sits on it.
	var b := _ball()
	var bs := _project(Vector2(b.x, b.y), b.z)
	var br := maxf(3.0, 0.2 * bs.z * FIGURE) + 4.0
	keep.append(Rect2(bs.x - br, bs.y - br, br * 2.0, br * 2.0))
	_draw_tags(_named(), keep)


## Where each name was drawn at the last freeze frame: {id, box, head} (tests).
var tag_log: Array = []


## A name for each of those men, on the overlay: white on a dark backing with his club's
## colour down its edge, pinned to his head - over it, or under his boots, or beside his
## head when another name, the ball (keep: boxes to stay off), the title bar or the call is
## in the way. Only for a man whose head is in the picture.
func _draw_tags(men: Array, keep: Array = []) -> void:
	var font: Font = UiKit.BOLD
	var fs := int(clampf(minf(size.x / 26.0, size.y / 50.0), 12.0, 20.0))
	var bar := size.y * 0.075
	var floor_y := size.y - maxf(_room(), bar)
	var placed: Array = keep.duplicate()
	tag_log.clear()
	for t in men:
		var at := _pos(t)
		var head := _project(at, _lift(t) + _head_top(t))
		var feet := _project(at, _lift(t))
		if head.x < 0.0 or head.x > size.x or head.y > floor_y:
			continue
		var name := str(t["name"])
		var box_size := Vector2(font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + 13.0, fs + 7.0)
		var shoulder := SHOULDER * FIGURE * feet.z
		var mid_x := clampf(head.x - box_size.x * 0.5, 4.0, size.x - box_size.x - 4.0)
		var spots := [Vector2(mid_x, head.y - box_size.y - 4.0), Vector2(mid_x, feet.y + 5.0),
				Vector2(head.x + shoulder + 4.0, head.y), Vector2(head.x - shoulder - 4.0 - box_size.x, head.y)]
		var box := Rect2()
		for spot in spots:
			var r := Rect2(spot, box_size)
			if r.position.x < 2.0 or r.end.x > size.x - 2.0 or r.position.y < bar + 2.0 or r.end.y > floor_y - 2.0:
				continue
			if placed.any(func(q): return (q as Rect2).intersects(r)):
				continue
			box = r
			break
		if not box.has_area():
			# Nowhere free: over his head, held inside the picture.
			box = Rect2(Vector2(mid_x, clampf(head.y - box_size.y - 4.0, bar + 2.0, maxf(bar + 2.0, floor_y - box_size.y - 2.0))), box_size)
		placed.append(box)
		tag_log.append({"id": str(t.get("id", "")), "box": box, "head": Vector2(head.x, head.y), "feet": Vector2(feet.x, feet.y)})
		var cols: Array = _colours[int(t["side"])] if int(t["side"]) < _colours.size() else []
		_ui.draw_rect(box, Color(0.03, 0.04, 0.05, 0.82), true)
		_ui.draw_rect(Rect2(box.position, Vector2(4.0, box.size.y)), (cols[0] as Color) if not cols.is_empty() else Color.WHITE, true)
		_ui.draw_string(font, box.position + Vector2(9.0, fs + 1.0), name, HORIZONTAL_ALIGNMENT_LEFT, -1, fs,
				Color(1, 1, 1, 0.7) if bool(t.get("dim", false)) else Color(1, 1, 1))


## Letterbox bars slide in on the cut; the call's heading rides the top one.
func _draw_bars(fade: float) -> void:
	var bar := size.y * 0.075 * _ease(fade)
	_ui.draw_rect(Rect2(0, 0, size.x, bar), Color(0, 0, 0), true)
	_ui.draw_rect(Rect2(0, size.y - bar, size.x, bar), Color(0, 0, 0), true)
	if title != "" and fade >= 1.0:
		var font: Font = UiKit.BOLD
		var fs := int(clampf(size.x / 24.0, 13.0, 18.0))
		var tw := font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		_ui.draw_string(font, Vector2(maxf(12.0, (size.x - tw) * 0.5), bar * 0.5 + fs * 0.36), title,
				HORIZONTAL_ALIGNMENT_LEFT, size.x - 24.0, fs, Color(1, 1, 1, 0.92))


func _readable_on(bg: Color) -> Color:
	var lum := 0.299 * bg.r + 0.587 * bg.g + 0.114 * bg.b
	return Color(0.08, 0.08, 0.1) if lum > 0.55 else Color(1, 1, 1)


## The frame of a figure's move to draw: the one asked for, held on the last
## when a move runs out (logged for tests; see log_frames).
static func figure_frame(info: Dictionary, wanted: int, anim: String, facing: String) -> int:
	var frames := int(info["frames"])
	if log_frames:
		frame_log.append({"anim": anim, "facing": facing, "frames": frames, "wanted": wanted, "info": info})
	return clampi(wanted, 0, frames - 1)
