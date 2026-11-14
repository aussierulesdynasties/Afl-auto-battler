class_name PitchView
extends Control
## Top-down animated AFL oval.
##
## MatchSim produces a deterministic event log up front; this view replays it.
## It only draws: MatchDirector turns the log into movement (who leads, who
## chases, how the ball travels, how stoppages set up) and MatchMotion moves
## the players. The log stays the truth - the view decides how an event looks,
## never whether it happens - and each event is released through
## event_played at the moment it visibly happens.

signal event_played(ev: Dictionary)
signal finished
## The sides have changed ends: `period` is the one now being played.
signal ends_changed(period: int)

const GOAL_LINE_M := 85.0
const ASPECT := 1.28            # oval length : width, close to a real AFL ground

var result := {}
var home_code := ""
var away_code := ""
var events: Array = []

var playing := false
## A full match is ~1,200 events; 4x plays it in a few minutes. 1x-8x offered.
var speed := 4.0
## A broadcast-style camera that follows play. Off, the whole oval shows.
var camera_enabled := true
## Smooth the edges of the lines and outlines drawn here (the oval, arcs,
## rings, token outlines). Fills stay as they are.
var antialias := true
## The ground runs top to bottom (director, 2026-10-14: "turn the oval upright" on
## a phone in portrait), goals at the top and the bottom, the whole ground in
## view. It is the same picture turned a quarter turn: the home side kicks up
## the screen in the first quarter where it kicked to the right. Everything is
## worked out as it is for the ground lying flat (the "flat" frame: _flat_size,
## _w2s_flat) and turned at the end (_to_screen); names, numbers and the ball's
## height stay upright. The match screen sets it; PC and landscape leave it off.
var upright := false:
	set(v):
		if v != upright:
			upright = v
			_nudge = PackedVector2Array()
			_disc = PackedVector2Array()
			_disc_k = PackedFloat32Array()
			_cam = _clamp_cam(_cam)
			queue_redraw()

var director := MatchDirector.new()
var _cam := Vector2.ZERO
var _zoom := 1.0
var _drawn_cam := Vector2.INF
var _drawn_zoom := -1.0
## Teams change ends every quarter. The director plays the match in its own
## frame (the home side always kicks toward +x); the view mirrors that frame
## in the 2nd and 4th quarters so the home side attacks the other end.
## Counts periods of play: every break (quarter time, half time, three
## quarter time, and the extra-time breaks) is a change of ends.
var period := 1
## A break has been played and the sides have not yet changed ends: they swap when
## the next period restarts (the players walking to the centre), not at the siren,
## when the clock still shows the quarter just ended. Never after the last siren.
var _flip_pending := false
## Your people on the oval. `rings` are the players of yours with a call on them
## or a run promised (MatchRings): a thin ring on their token. A name goes over
## whoever has just kicked a goal, and over one of the ringed players when he has
## the ball. The name is kept in real seconds, not match time, so it can be read
## at any playback speed; the screen sets the rings, the view only draws.
var rings := {}
## Tired and hurt players (PlayerMarks.build): pid -> {mark, words}. A short
## mark beside the disc on the oval and beside the name in the bench's drawer; words
## on a long press.
var marks := {}
## The long press: where the finger is down and since when (-1 for none), and
## the words it brought up ({text, at, left}).
const HOLD_SECS := 0.45
const HOLD_SLOP := 14.0
const TIP_SECS := 2.5
var _hold_at := Vector2.ZERO
var _hold_serial := 0
var _held := false
var tip := {}
var _caption := {}             # {tok, text, left, goal, turnover, side}
var _poss_side := -1           # who had the ball at the last possession event
var _restarted := true         # the next possession comes from a restart
var _shake := 0.0              # seconds of goal shake left
var shake_share := SHAKE_SHARE # the shake's size (captures compare strengths)
var _last_actor := -1
const CAPTION_GOAL := 1.8
const CAPTION_TOUCH := 1.0
## A change of possession in open play is said in words over the player who won
## it (ROADMAP §1.11: a clear turnover cue; tackles where the ball is kept or
## held in are not turnovers and carry no label).
const CAPTION_TURNOVER := 1.1
## A clanger that says why ("Kick to space") over the player who erred: a little
## longer than "Turnover", it is a sentence.
const CAPTION_WHY := 1.5
## The goal's shake, the only one in the game: short, gone in under a fifth of a
## second. Its size is a share of the oval's height, so it reads the same on a phone
## and a PC. Director, 2026-10-13: "reduce screenshake" - about 40% of the old size
## (0.025), 60% of the old time (0.3), never more than the share below as a hard cap
## (about 4 px on a phone), and a new goal restarts the shake, it never adds to it.
## This is the one place to change its strength.
const SHAKE_TIME := 0.18
const SHAKE_SHARE := 0.01
const SHAKE_MAX_PX := 4.0   # and never more than this, on any screen
## What restarts play: whoever wins the ball after one of these has not turned
## it over.
const RESTARTS := ["goal", "behind", "quarter", "ballup", "throwin", "free", "fifty",
		"last_disposal", "out_on_full"]
## The turf is green in both appearances, so the ring is the dark theme's text
## colour fixed, not UiKit.TEXT, which turns dark in light mode.
const RING_COLOUR := Color(0.945, 0.933, 0.902)
## A player's disc, half as big again as it was (director, 2026-11-12: "Bigger
## discs, bench drawer", about 1.5x, the jumper number readable): never under a
## radius of 13.5 px (a 27 px disc on a phone; it was 9 and 18), and DISC_SHARE of
## the oval's half-width where the ground is bigger (it was 0.030). The number
## grows with it, up to NUMBER_MAX px.
const TOKEN_MIN := 13.5
const DISC_SHARE := 0.045
const NUMBER_MAX := 22.0
## Shrink in packs (director, 2026-11-12: "Shrink in packs"; the gain "big discs
## most of the time", the cost "sizes change during play, and numbers in a pack
## are small"). A disc is the full size above in the open and beside one other
## player: a pair is drawn apart, as it always was. In a pack it is drawn smaller:
## its radius is PACK_FIT of the distance to the second-nearest other player on
## the screen (pack_radius), so it starts to shrink once two players are within a
## disc and a half's radius of it, and it is never under the old size (a radius of
## SMALL_MIN px on a phone, SMALL_SHARE of the oval's half-width where the ground
## is bigger: two thirds of the full size), which it reaches with two players
## within a full radius. One function for both sides, read from where the players
## are, not from where the discs are drawn. The size eases: it crosses the whole
## range, full to small or back, in no less than RESIZE_SECS of the match's own
## seconds, the clock the draw-apart moves on (at 1x on a phone, 0.62 px in a 30th
## of a second), with reduced motion as without (a size that jumped would flicker).
## Measured on a phone over five games (tests/test_match_motion.gd): 57% of
## disc-frames at the full size. The measured alternatives: sized from the nearest
## player so a pair just touches, 19%; from the nearest, two thirds of the gap,
## 31%; from the second-nearest, half the gap, 42%; three quarters of it, 63%,
## with twice the frames under the visibility floor.
const PACK_FIT := 2.0 / 3.0
const SMALL_MIN := 9.0
const SMALL_SHARE := 0.030
const RESIZE_SECS := 0.4
## How far each disc is between the small size (0) and the full size (1), as drawn.
var _disc_k := PackedFloat32Array()
## The ball's last few positions on the turf, for a short trail behind it.
const TRAIL_N := 14
var _trail: Array = []
## Each side's home kit (GameDB.club_guernsey): the token wears the club's
## design, not just its colours, so the two sides read apart at a glance.
var _kits: Array = [{}, {}]
## True when the two home kits looked alike on a disc and the away side wears its
## clash strip, its own kit's two colours changed over (kits_for).
var clash := false
## Two disc bases this close (UiKit.colour_distance, the measure the club inks
## use) are alike on the turf. A little wider than UiKit.INK_CLASH (25): a disc is
## an 18 px dot on green, where two dark bases merge sooner than two names side by
## side do (Fremantle's purple and Melbourne's navy are 26.6 apart and read as one
## side in a pack: audit frame fre_mel_phone 005).
const DISC_CLASH := 40.0
## Discs that would overlap are drawn apart, so both numbers show. Drawing only:
## the players stay where the match has them. NUDGE_GAP is the distance two drawn
## centres are pushed toward, in disc diameters; each frame the nudge eases back
## by NUDGE_EASE and is pushed out again only as far as it must be, starting from
## where the discs were drawn last, so a pair keeps its sides and does not jitter.
## The view stays truthful: a disc is never drawn more than NUDGE_CAP (in disc
## diameters at the small size, small_radius: half the old disc's width, 4.3 m on
## a phone, whatever size the disc is drawn at) from where its player is, so in a thick pack
## discs still overlap, and the draw order keeps the ball carrier and the two
## opponents nearest him on top (lead, 2026-10-14, provisional until the director
## looks). nudge_full lifts the cap, for the comparison capture only: every disc
## fully apart, at the cost of a disc sitting up to 17 m from its player on a phone.
const NUDGE_GAP := 1.0
const NUDGE_CAP := 0.5
static var nudge_full := false
const NUDGE_EASE := 0.85
const NUDGE_PASSES := 24
## The draw-apart moves a disc no faster than a walk (MatchMotion.WALK, in the
## match's own seconds): two discs closing on each other part over a moment and
## never snap across (the motion critic, 2026-10-18: a disc hopping 4 m in one
## frame as a pile re-sorted). Match seconds played since the last layout; -1
## until the first one, which places the discs at once.
var _nudge_h := -1.0
var _nudge := PackedVector2Array()
var _disc := PackedVector2Array()   # where each token is drawn, in pixels
## The bench is in a drawer (director, 2026-11-12): a tab on the oval's bottom edge
## opens both benches, and nothing of the bench is drawn over the ground or the
## stands. BenchDrawer is this view's own child.
var _bench: BenchDrawer
## The stadium round the oval, from the replay's parts (director, 2026-11-12:
## "Replay stadium everywhere"): OvalStadium, built once a match.
var _stadium := OvalStadium.new()
## What the last frame drew of it, for tests and captures: the time of day, the
## flags flying (0 without wind) and which way they stream (+1 or -1 along the
## ground as it is drawn).
var stadium_drawn := {}
## The fence between the turf and the front row.
const FENCE_COLOUR := Color(0.36, 0.33, 0.29)
## PROTOTYPE, gated by the director's phone (audit §8 Phase 3.3): the few
## players nearest the ball drawn as small footballers from the vignette
## sheets, over their tokens. Settings > Match view; off by default. If it
## reads and holds 60 fps on the phone it becomes the view; otherwise it goes.
var mini_figures := false
const FIGURES_NEAR_BALL := 6
const FIGURE_HEIGHT := 1.8        # figure height in token radii (tr 13.5 = 24 px)
var _figs: MiniFigures
var _looks := {}
## The 3D oval (row 197; director 2026-11-14, "True 3D oval"): the same director's players on
## a real 3D ground (Oval3D), rendered at the screen's own pixels and shown in place of the
## flat drawing. Settings > Match view; the match screen sets it before setup().
var three_d := false
var _oval3d: Oval3D = null
var _vp3d: SubViewport = null
var _view3d: TextureRect = null
const CAM3D_UP := 18.0
const CAM3D_BACK := 28.0


## The figures' own layer: the figure shader is a material on a CanvasItem,
## so they cannot share the oval's drawing.
class MiniFigures extends Control:
	var slots: Array = []

	func _draw() -> void:
		for s in slots:
			StoppageVignette.draw_frame(self, s["feet"], s["info"], int(s["frame"]), float(s["k"]),
					s["colour"], bool(s["mirror"]), s["number"], Transform2D.IDENTITY, str(s["hair"]), int(s.get("face", -1)),
					int(s.get("ink", 0)))


func _ready() -> void:
	# The oval takes a long press on a disc (a tired or hurt player's words);
	# everything else passes on to the screen.
	mouse_filter = Control.MOUSE_FILTER_PASS
	clip_contents = true
	_figs = MiniFigures.new()
	_figs.name = "MiniFigures"
	_figs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_figs.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_figs)
	_bench = BenchDrawer.new()
	_bench.name = "BenchDrawer"
	_bench.view = self
	add_child(_bench)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
func setup(p_result: Dictionary) -> void:
	result = p_result
	# Our own list, so appended segments never touch the caller's result.
	events = (p_result.get("events", []) as Array).duplicate()
	home_code = str(p_result.get("home", ""))
	away_code = str(p_result.get("away", ""))
	_kits = kits_for(home_code, away_code)
	clash = bool((_kits[1] as Dictionary).get("clash", false))
	_nudge = PackedVector2Array()
	_disc = PackedVector2Array()
	_order = []
	_flip_pending = false
	_trail = []
	mini_figures = GameState.match_figures_on()
	_looks = {}
	if _figs != null:
		_figs.material = StoppageVignette.figure_material(_kits, _figs.material as ShaderMaterial)
		_figs.slots = []
	playing = false
	director = MatchDirector.new()
	director.setup(p_result, events)
	_setup_3d()
	if _bench != null:
		# A new match: the drawer shut, its tab there when this match names a bench.
		_bench.close()
		_bench.sync()
	period = 1
	_caption = {}
	_press_said = [false, false]
	_press_banner = {}
	_zone_fade = [0.0, 0.0]
	_corr_fade = [0.0, 0.0]
	_stop_fade = [0.0, 0.0]
	_open_fade = [0.0, 0.0]
	_stop_ring = [{}, {}]
	_open_ring = [{}, {}]
	_open_leaving = [false, false]
	_open_wait = [0.0, 0.0]
	_open_on = [0.0, 0.0]
	_stop_on = [0.0, 0.0]
	_mark_ball = Vector2.INF
	_ev_idx = 0
	_last_actor = -1
	_poss_side = -1
	_restarted = true
	_cam = Vector2.ZERO
	_zoom = _target_zoom()
	set_process(true)
	queue_redraw()


func append_events(new_events: Array, timeline: Array = []) -> void:
	events.append_array(new_events)
	if not timeline.is_empty() and director != null:
		director.set_timeline(timeline)
	queue_redraw()


# ---------------------------------------------------------------------------
# The 3D oval
# ---------------------------------------------------------------------------
## A new match on the 3D oval: a fresh scene for this director (its players, kits and
## stands), or the flat oval again when three_d is off.
func _setup_3d() -> void:
	if _oval3d != null:
		_oval3d.queue_free()
		_oval3d = null
	if not three_d:
		if _vp3d != null:
			_vp3d.queue_free()
			_view3d.queue_free()
			_vp3d = null
			_view3d = null
		if _figs != null:
			_figs.visible = true
		return
	if _vp3d == null:
		_vp3d = SubViewport.new()
		_vp3d.name = "Oval3DViewport"
		_vp3d.own_world_3d = true
		_vp3d.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		add_child(_vp3d)
		_view3d = TextureRect.new()
		_view3d.name = "Oval3DView"
		_view3d.texture = _vp3d.get_texture()
		_view3d.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_view3d.stretch_mode = TextureRect.STRETCH_SCALE
		_view3d.mouse_filter = Control.MOUSE_FILTER_IGNORE
		# Under this view's own drawing (the overlays), which a child otherwise covers.
		_view3d.show_behind_parent = true
		_view3d.set_anchors_preset(Control.PRESET_FULL_RECT)
		add_child(_view3d)
		# Under the bench drawer and anything else the view puts over the oval.
		move_child(_view3d, 0)
	if _figs != null:
		_figs.visible = false
	_oval3d = Oval3D.new()
	_vp3d.add_child(_oval3d)
	_oval3d.build(director, home_code, away_code)
	_make_paint_3d()
	_oval3d.set_ends(end_sign(period))
	_fit_3d()
	_sync_3d(0.0)
	_paint_ground_3d()
	queue_redraw()


## The 3D picture is drawn at the screen's own pixels, not the stretched 2D canvas's
## (on a phone the canvas is about 485 px wide; the screen 1080).
func _fit_3d() -> void:
	var vis := get_viewport().get_visible_rect().size if is_inside_tree() else Vector2.ZERO
	var k := 1.0
	if vis.x > 0.0:
		k = clampf(float(DisplayServer.window_get_size().x) / vis.x, 1.0, 3.0)
	var want := Vector2i(maxi(8, int(size.x * k)), maxi(8, int(size.y * k)))
	if _vp3d.size != want:
		_vp3d.size = want


## `dt` is match time (the play speed applied), so the bodies run at the director's pace.
func _sync_3d(dt: float) -> void:
	_fit_3d()
	_oval3d.sync(dt)
	if not is_inside_tree():
		return
	# Portrait: from behind the play, the ground running up the screen; wide: from the wing.
	# The match screen gives the oval about a third of a phone, so the camera sits closer
	# than the full-screen prototype's (34 m up, 52 m back): a player stands about a tenth
	# of the view tall.
	if size.y > size.x:
		_oval3d.aim_end(CAM3D_UP, CAM3D_BACK)
	else:
		_oval3d.aim_wing(CAM3D_UP, CAM3D_BACK * 1.3)


## The overlays on the 3D view (director, 2026-11-15: "Overlays first"). The flat
## oval's calls, names and markings are drawn over the 3D picture, each at the
## point of the ground (or the body) the 3D camera puts it: a footballer counts as
## a disc round his middle, half his height across, so the captions, names and
## long-press tips that step clear of discs step clear of the bodies; the marks
## and press washes are laid on the grass in perspective.
const BODY3D_H := 1.9          # metres: a footballer's height, feet to crown
const BODY3D_CLEAR := 1.0      # metres: a ring on the grass clears a player by this
const RING3D_YOURS := 1.0      # metres: your-people ring, outside the club ring (0.72)
const RING3D_ACTOR := 1.3      # ...and the man on the ball's, outside that
var _r3d := PackedFloat32Array()   # each body's drawn half-height, in pixels
var _tr3d := 0.0                   # a body's half-height where the camera looks
const PRESS3D_K := 0.5        # the press wash in 3D, against the flat oval's (director 2026-11-15: "Lighten it")
const PAINT3D_Y := 0.02       # metres: the ground paint, over the turf, under the club rings (0.03)
var _paint3d: ImmediateMesh = null
var _paint_mat: StandardMaterial3D = null    # the wash and marks: lit like the turf
var _paint_glow: StandardMaterial3D = null   # the rings and the flash: bright as on the flat oval
var _paint_want: Material = null
var _painting = null                         # the material of the surface being laid, or null


## A point of the 3D ground (Oval3D's own frame: metres up the ground, up, across)
## in this view's pixels; far off the view when it is behind the camera.
func _project3d(v: Vector3) -> Vector2:
	var cam := _oval3d.camera
	var w := _oval3d.global_transform * v
	if cam.is_position_behind(w):
		return Vector2(-100000.0, -100000.0)
	return cam.unproject_position(w) * (size / Vector2(_vp3d.size))


## Every body as a disc on the screen, round his middle: _disc, _r3d and the
## size the names and captions are worked out at.
func _layout_3d() -> void:
	var n := director.tokens.size()
	_disc.resize(n)
	_r3d.resize(n)
	_disc_k.resize(n)
	_disc_k.fill(1.0)
	for i in range(n):
		var p: Vector2 = director.tokens[i]["pos"]
		var feet := _project3d(Vector3(p.x, 0.0, p.y))
		var head := _project3d(Vector3(p.x, BODY3D_H, p.y))
		_disc[i] = (feet + head) * 0.5
		_r3d[i] = maxf(3.0, feet.distance_to(head) * 0.5)
	var at := _oval3d._look
	var f := _project3d(Vector3(at.x, 0.0, at.z))
	var h := _project3d(Vector3(at.x, BODY3D_H, at.z))
	_tr3d = maxf(6.0, f.distance_to(h) * 0.5)


## A shape on the grass (corners in ground metres, a colour each, convex): flat, drawn
## in the ground's frame; in 3D, laid on the turf as part of the ground paint mesh,
## so a body or a post in front of it hides it as it would hide the grass.
func _ground_polygon(pts: Array, cols: PackedColorArray) -> void:
	if _oval3d == null or _paint3d == null:
		var flat := PackedVector2Array()
		for p in pts:
			flat.append(_w2s_flat(p))
		draw_polygon(flat, cols)
		return
	var want: Material = _paint_want if _paint_want != null else _paint_mat
	if _painting != want:
		if _painting != null:
			_paint3d.surface_end()
		_paint3d.surface_begin(Mesh.PRIMITIVE_TRIANGLES, want)
		_painting = want
	for i in range(1, pts.size() - 1):
		for k in [0, i, i + 1]:
			var p: Vector2 = pts[k]
			_paint3d.surface_set_color(cols[k])
			_paint3d.surface_add_vertex(Vector3(p.x, PAINT3D_Y, p.y))


## A band on the grass round `at`, `r` metres out and `width` metres wide.
func _ground_ring(at: Vector2, r: float, col: Color, width: float) -> void:
	var cols := PackedColorArray([col, col, col, col])
	var n := 40
	for i in range(n):
		var a0 := Vector2.from_angle(TAU * float(i) / float(n))
		var a1 := Vector2.from_angle(TAU * float(i + 1) / float(n))
		_ground_polygon([at + a0 * (r - width * 0.5), at + a1 * (r - width * 0.5),
				at + a1 * (r + width * 0.5), at + a0 * (r + width * 0.5)], cols)


## The press wash in 3D: the same slices up the ground as the flat oval's, each the
## oval's width across, laid on the grass.
func _draw_press_zone_3d() -> void:
	for side in [0, 1]:
		var fade := ease_fade(float(_zone_fade[side]))
		if fade <= 0.003:
			continue
		var base := press_zone_colour(home_code if side == 0 else away_code)
		var dir := MatchDirector._dir(side)
		var n := 56
		for i in range(n):
			var wx0 := lerpf(-MatchMotion.HALF_LEN, MatchMotion.HALF_LEN, float(i) / float(n))
			var wx1 := lerpf(-MatchMotion.HALF_LEN, MatchMotion.HALF_LEN, float(i + 1) / float(n))
			var k0 := MatchDirector.press_zone_field(wx0 * dir)
			var k1 := MatchDirector.press_zone_field(wx1 * dir)
			if k0 <= 0.002 and k1 <= 0.002:
				continue
			var pts := []
			var cols := PackedColorArray()
			for e in [-1.0, 1.0]:
				for q in range(4):
					var t := float(q) / 3.0 if e < 0.0 else 1.0 - float(q) / 3.0
					var x := lerpf(wx0, wx1, t)
					var u := clampf(x / MatchMotion.HALF_LEN, -1.0, 1.0)
					pts.append(Vector2(x, e * MatchMotion.HALF_WID * sqrt(1.0 - u * u)))
					cols.append(Color(base.r, base.g, base.b, PRESS_ZONE_ALPHA * PRESS3D_K * fade * lerpf(k0, k1, t)))
			_ground_polygon(pts, cols)


## The ground paint in 3D, laid each frame after the bodies move: the press wash, the
## coach's marks, your people's rings, the ring round the man on the ball and the
## goal flash, all on the turf under the bodies, as the flat oval draws them under
## the discs.
func _paint_ground_3d() -> void:
	if _paint3d == null:
		return
	_paint3d.clear_surfaces()
	_painting = null
	_paint_want = _paint_mat
	_layout_3d()
	drawn_layers = ["3d"]
	_draw_press_zone_3d()
	drawn_layers.append("press")
	if _draw_marks(token_radius()) > 0:
		drawn_layers.append("marks")
	_paint_want = _paint_glow
	# Your people: a white band outside his club ring.
	for t in director.tokens:
		if float(t["down"]) <= 0.0 and rings.has(str(t.get("pid", ""))):
			_ground_ring(t["pos"], RING3D_YOURS, Color(RING_COLOUR, 0.9), 0.14)
	var act := director.actor
	if act >= 0 and act < director.tokens.size():
		_ground_ring(director.tokens[act]["pos"], RING3D_ACTOR, Color(1, 1, 0.55, 0.95), 0.18)
	var fl := director.flash
	if not fl.is_empty():
		var t2 := 1.0 - clampf(float(fl["left"]) / 0.9, 0.0, 1.0)
		var col := Color(1.0, 0.92, 0.35) if fl["goal"] else Color(0.85, 0.9, 1.0)
		col.a = (1.0 - t2) * 0.85
		_ground_ring(fl["pos"], lerpf(1.5, 14.0, t2), col, 0.5)
	if _painting != null:
		_paint3d.surface_end()
		_painting = null
	drawn_layers.append("discs")


## The paint's mesh, on the 3D ground (it turns with the ground at a change of ends).
func _make_paint_3d() -> void:
	_paint3d = ImmediateMesh.new()
	_paint_mat = StandardMaterial3D.new()
	# Lit like the turf, so a player's shadow falls across the paint as across the grass.
	_paint_mat.roughness = 1.0
	_paint_mat.metallic_specular = 0.0
	_paint_mat.vertex_color_use_as_albedo = true
	_paint_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_paint_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_paint_glow = _paint_mat.duplicate()
	_paint_glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	var mi := MeshInstance3D.new()
	mi.name = "GroundPaint"
	mi.mesh = _paint3d
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_oval3d.add_child(mi)


## Over the 3D picture: the names, the caption, the press line and the long-press tip.
func _draw_3d() -> void:
	if _vp3d == null or not is_inside_tree():
		return
	draw_set_transform(shake_offset() if _shake > 0.0 else Vector2.ZERO)
	_layout_3d()
	var tr := token_radius()
	_draw_role_labels(tr)
	_draw_caption(tr)
	_draw_press_banner()
	_draw_tip()


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------
func play() -> void:
	if director.idle():
		# Nothing new to show (a moment right where the last one left off):
		# say so, or the match screen waits for a finish that never comes
		# and the match freezes with the next call unasked.
		playing = false
		finished.emit()
		return
	playing = true
	set_process(true)


func pause() -> void:
	playing = false


func toggle() -> void:
	if playing:
		pause()
	else:
		play()


func restart() -> void:
	setup(result)
	play()


func set_speed(s: float) -> void:
	speed = clampf(s, 0.25, 8.0)


## Jump to the end of what has been logged: the rest of the events are applied
## without animation (the scene reads the final result itself) and the view
## settles.
func skip_to_end() -> void:
	playing = false
	for ev in director.flush():
		_track_quarter(ev)
	_caption = {}
	queue_redraw()
	finished.emit()


## Release everything logged at once, each event to the match screen as if it
## had played (the feed and the scoreboard catch up), without the animation.
## Unlike skip_to_end the screen hears every event; finished is the caller's.
func release_all() -> void:
	playing = false
	for ev in director.flush():
		_track_quarter(ev)
		event_played.emit(ev)
	_caption = {}
	queue_redraw()


## Events released to the match screen so far.
func current_index() -> int:
	return director.emitted


func progress() -> float:
	return float(director.emitted) / float(maxi(1, events.size()))


func _process(delta: float) -> void:
	if playing:
		if _nudge_h >= 0.0:
			_nudge_h += delta * speed * MatchDirector.TEMPO
		var out := director.advance(delta * speed)
		for ev in out:
			_track_quarter(ev)
			_name_the_scorer(ev)
			_cue_turnover(ev)
			_press_cue(ev)
			event_played.emit(ev)
			if str((ev as Dictionary).get("kind", "")) == "final":
				playing = false
				finished.emit()
				break
		if playing and director.idle():
			playing = false
			finished.emit()
		if _flip_pending and director.mode != "break":
			# The next period is setting up: now the sides change ends.
			_change_ends()
		_follow_ball()
	_name_the_ball_carrier()
	_age_caption(delta)
	_step_zone_fade(delta)
	_step_marks(delta)
	if not _press_banner.is_empty():
		_press_banner["left"] = float(_press_banner["left"]) - delta
		if float(_press_banner["left"]) <= 0.0:
			_press_banner = {}
	if _shake > 0.0:
		_shake = maxf(0.0, _shake - delta)
		queue_redraw()
	_update_camera(delta)
	if _oval3d != null:
		_sync_3d(delta * speed if playing else 0.0)
		_paint_ground_3d()
		queue_redraw()
		return
	if playing or _cam.distance_to(_drawn_cam) > 0.05 or absf(_zoom - _drawn_zoom) > 0.002 \
			or not director.flash.is_empty() or not _caption.is_empty() or not _press_banner.is_empty() \
			or float(_zone_fade[0]) > 0.0 or float(_zone_fade[1]) > 0.0 \
			or director.press_zone_on(0) or director.press_zone_on(1) or marks_live():
		queue_redraw()


# ---------------------------------------------------------------------------
# Your people on the oval
# ---------------------------------------------------------------------------
## Ring these players (ids); [] clears them.
func set_rings(ids: Array) -> void:
	var next := {}
	for id in ids:
		next[str(id)] = true
	var a := rings.keys()
	var b := next.keys()
	a.sort()
	b.sort()
	if a == b:
		return
	rings = next
	queue_redraw()


func set_marks(next: Dictionary) -> void:
	if next == marks:
		return
	marks = next
	if _bench != null:
		_bench.sync()
	queue_redraw()


## A long press on a marked disc says what the mark means; a tap or a drag
## does nothing here.
func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		if (e as InputEventMouseButton).pressed:
			_hold_at = (e as InputEventMouseButton).position
			_held = true
			_hold_serial += 1
			var serial := _hold_serial
			get_tree().create_timer(HOLD_SECS).timeout.connect(func():
				if _held and serial == _hold_serial:
					show_tip_at(_hold_at))
		else:
			_held = false
			if not tip.is_empty():
				var serial2 := _hold_serial
				get_tree().create_timer(TIP_SECS).timeout.connect(func():
					if serial2 == _hold_serial and not tip.is_empty():
						tip = {}
						queue_redraw())
	elif e is InputEventMouseMotion and _held:
		if (e as InputEventMouseMotion).position.distance_to(_hold_at) > HOLD_SLOP:
			_held = false


## The marked player under `p` (a point in this view): {pid, words, at, r}, or
## {} for none: the discs on the oval (the bench's marks are in its drawer).
func marked_at(p: Vector2) -> Dictionary:
	if marks.is_empty() or director == null:
		return {}
	var id := disc_at_point(p)
	if id >= 0:
		var pid2 := str(director.tokens[id].get("pid", ""))
		if marks.has(pid2):
			return {"pid": pid2, "words": PlayerMarks.words(marks[pid2], false), "at": _disc_at(id), "r": disc_radius(id)}
	return {}


## Put up the words for the marked player at `p`; false when there is none.
func show_tip_at(p: Vector2) -> bool:
	var hit := marked_at(p)
	if hit.is_empty():
		return false
	var who := GameDB.player_display_name_by_id(str(hit["pid"]), "")
	tip = {"text": str(hit["words"]), "name": who, "at": hit["at"], "r": hit["r"]}
	queue_redraw()
	return true


func ringed(pid: String) -> bool:
	return rings.has(pid)


## The name over a player right now, "" for none.
func caption_text() -> String:
	return str(_caption.get("text", ""))


## A goal puts its scorer's name on the oval, either side's.
func _name_the_scorer(ev: Dictionary) -> void:
	if str(ev.get("kind", "")) != "goal":
		return
	var tok := director.token_of(ev)
	if tok < 0 or tok >= director.tokens.size():
		return
	_caption = {"tok": tok, "text": str(director.tokens[tok].get("surname", "")),
			"left": CAPTION_GOAL, "goal": true}
	if GameState.screen_shake_on() and not Feel.reduced:
		_shake = SHAKE_TIME


## The ball changed hands in open play: "Turnover" over the player who won it.
## A forced turnover, a rebound and an intercept mark always are; otherwise
## the side with the ball changed without a restart in between. A goal's name
## is never covered.
## The first time a pressing side defends after setting its plan: its line, on
## the oval for a moment ("<Club> push up to press."), once a side a match.
func _press_cue(ev: Dictionary) -> void:
	var idx := _ev_idx
	_ev_idx += 1
	var presser := MatchNotes.press_trigger(result.get("timeline", []), idx, ev, _press_said)
	if presser < 0:
		return
	_press_said[presser] = true
	var code := str(result.get("home") if presser == 0 else result.get("away"))
	_press_banner = {"text": MatchNotes.press_line(code), "left": PRESS_BANNER_SECS, "side": presser}


func _cue_turnover(ev: Dictionary) -> void:
	var kind := str(ev.get("kind", ""))
	if RESTARTS.has(kind):
		_restarted = true
		return
	var side := int(ev.get("side", -1))
	if kind == "clanger":
		_cue_clanger(ev)
		return
	var won := kind == "pressure" or kind == "rebound" \
			or (kind == "mark" and bool(ev.get("intercept", false)))
	if side < 0 or not (won or MatchDirector.DISPOSALS.has(kind)):
		return
	var flipped := _poss_side >= 0 and side != _poss_side and not _restarted
	_poss_side = side
	_restarted = false
	if not (won or flipped):
		return
	if not _caption.is_empty() and (bool(_caption["goal"]) or bool(_caption.get("why", false))):
		return
	var tok := director.token_of(ev)
	if tok < 0 or tok >= director.tokens.size():
		return
	_caption = {"tok": tok, "text": "Turnover", "left": CAPTION_TURNOVER, "goal": false,
			"turnover": true, "side": side}


## A clanger with a cause names it over the player who
## erred, underlined in the club that has the ball now. Without a cause it says
## nothing, as before. A goal's name is never covered, and the turnover that
## follows does not cover it.
func _cue_clanger(ev: Dictionary) -> void:
	var words := MatchNotes.clanger_caption(str(ev.get("why", "")))
	if words == "" or (not _caption.is_empty() and bool(_caption["goal"])):
		return
	var tok := director.token_of(ev)
	if tok < 0 or tok >= director.tokens.size():
		return
	var side := int(ev.get("side", 0))
	_caption = {"tok": tok, "text": words, "left": CAPTION_WHY, "goal": false,
			"turnover": true, "why": true, "side": 1 - side}


## Whether the oval is shaking for a goal right now.
func shaking() -> bool:
	return _shake > 0.0


## The shake as an offset in pixels now: never longer than the share of the oval's
## height, whatever the screen size; zero with the shake off.
func shake_offset() -> Vector2:
	if _shake <= 0.0 or not GameState.screen_shake_on() or Feel.reduced:
		return Vector2.ZERO
	var k := _shake / SHAKE_TIME
	var t := SHAKE_TIME - _shake
	var amp := minf(pitch_rect().size.y * shake_share, SHAKE_MAX_PX)
	return (Vector2(sin(t * 83.0), cos(t * 61.0)) * amp * k).limit_length(amp)


## A ringed player of yours who gets the ball is named for a moment. A goal's
## name outranks that, and a name already showing is not restarted.
func _name_the_ball_carrier() -> void:
	var act := director.actor
	if act == _last_actor:
		return
	_last_actor = act
	if act < 0 or act >= director.tokens.size():
		return
	var t: Dictionary = director.tokens[act]
	if not rings.has(str(t.get("pid", ""))):
		return
	if not _caption.is_empty() and (bool(_caption["goal"]) or bool(_caption.get("turnover", false))
			or int(_caption["tok"]) == act):
		return
	_caption = {"tok": act, "text": str(t.get("surname", "")), "left": CAPTION_TOUCH, "goal": false}


func _age_caption(delta: float) -> void:
	if _caption.is_empty():
		return
	_caption["left"] = float(_caption["left"]) - delta
	if float(_caption["left"]) <= 0.0:
		_caption = {}
		queue_redraw()


## The ball's path over the last fraction of a second, in ground metres. A
## dead ball leaves no trail; a ball that has not moved adds nothing.
func _follow_ball() -> void:
	if director.ball.is_empty() or str(director.ball.get("mode", "dead")) == "dead":
		_trail.clear()
		return
	var pos: Vector2 = director.ball["pos"]
	if not _trail.is_empty() and (_trail[-1] as Vector2).distance_to(pos) < 0.05:
		return
	_trail.append(pos)
	while _trail.size() > TRAIL_N:
		_trail.pop_front()


## Every break the match screen plays is a change of ends, made when play
## restarts: the siren only marks it as owed. Play that follows a break (seen
## here when events are skipped, not watched) makes the change if the restart
## has not; the final siren never does.
func _track_quarter(ev: Dictionary) -> void:
	var kind := str(ev.get("kind", ""))
	if kind == "quarter":
		if _flip_pending:
			_change_ends()
		_flip_pending = true
	elif _flip_pending and not ["final", "sub", "moment", "injury"].has(kind):
		_change_ends()


func _change_ends() -> void:
	_flip_pending = false
	period += 1
	if _oval3d != null:
		_oval3d.set_ends(end_sign(period))
	# The picture mirrors along the ground's length, and so does each disc's nudge.
	for i in range(_nudge.size()):
		_nudge[i] = Vector2(_nudge[i].x, -_nudge[i].y) if upright else Vector2(-_nudge[i].x, _nudge[i].y)
	ends_changed.emit(period)
	queue_redraw()


## The painted 50s on each arc: about 7 m tall on the ground, never under the
## oval's 13 px text floor (row T3.R9).
const FIFTY_M := 7.0
const FIFTY_GAP := 4.0
## How far along the arc from the boundary each 50 sits, in metres.
const FIFTY_FROM_BOUNDARY_M := 16.0


static func fifty_font_size(px_per_m: float) -> int:
	return int(maxf(13.0, round(FIFTY_M * px_per_m)))


## The goal square at the end a side kicks to is drawn in that side's colour,
## heavier than the ground's white lines, and filled. The 50 m arc stays white.
const END_LINE_W := 3.0
const END_FILL_ALPHA := 0.55
## A kit colour darker than this is lifted to it, so navy, brown and black read
## on the turf; a kit with no hue at all is drawn black or white, as its body is.
const END_MIN_V := 0.92
const END_MIN_S := 0.2
const END_BLACK := Color(0.05, 0.05, 0.07)


## The colour of the goal square at the end a side kicks to: the base colour of the kit
## its discs wear (so the end matches the players attacking it, clash strip
## included), lifted until it reads on the grass.
static func end_colour(kit: Dictionary) -> Color:
	var base: Color = kit.get("base", Color.WHITE)
	var pick := base
	if pick.s < END_MIN_S:
		# A black or white body (St Kilda): the kit's next colour with a hue.
		for key in ["pattern", "ring"]:
			var other = kit.get(key, null)
			if other is Color and (other as Color).s >= END_MIN_S:
				pick = other
				break
	if pick.s < END_MIN_S:
		# No hue anywhere in the kit (Collingwood): black for a dark body, else white.
		return END_BLACK if base.v < 0.5 else Color.WHITE
	return Color.from_hsv(pick.h, clampf(pick.s, 0.55, 0.9), maxf(pick.v, END_MIN_V))


## The two kits the discs wear. The home side wears its own. The away side does
## too unless its base colour looks like the home side's on a disc (DISC_CLASH,
## UiKit.colour_distance between the two bases): then it wears its clash strip,
## its own kit with the two colours changed over (Melbourne red with a navy yoke,
## Richmond yellow with a black sash, West Coast gold), as the real clubs do.
## Only the club's own kit colours are ever used (lead, 2026-10-14: UiKit's
## second inks are lifted for text and on a disc were not the club's colours). A
## kit whose pattern colour is no farther from the home base than its base
## (a created club, say) is left as it is: no colour is invented.
static func kits_for(home: String, away: String) -> Array:
	var h: Dictionary = with_trim(home, GameDB.club_guernsey(home))
	var a: Dictionary = with_trim(away, GameDB.club_guernsey(away))
	if disc_distance(h, a) >= DISC_CLASH:
		return [h, a]
	# Too alike on the turf: the away side tries its clash strips (its own kit's
	# two colours changed over; for a three-colour club its third colour as the
	# body) and wears the one farthest from the home side's disc.
	var best: Dictionary = a
	var best_d := disc_distance(h, a)
	var options := clash_options(away, a)
	for c in options:
		var d := disc_distance(h, c)
		if d > best_d + 0.01:
			best = c
			best_d = d
	if best != a:
		best["clash"] = true
	return [h, best]


## The away side's clash strips: the kit's base and pattern changed over, and
## (only for a club whose third colour is a real one) the third colour as the
## body with the base as the pattern. Only the club's own colours are used.
static func clash_options(code: String, kit: Dictionary) -> Array:
	var out := []
	var base: Color = kit.get("base", Color.WHITE)
	var pat: Color = kit.get("pattern", Color.DIM_GRAY)
	if UiKit.colour_distance(base, pat) > 12.0:
		var sw: Dictionary = kit.duplicate()
		sw["base"] = pat
		sw["pattern"] = base
		out.append(with_trim(code, sw, true))
	# A white clash strip, as the real clubs wear (Melbourne, Hawthorn, Essendon):
	# only for a club whose third colour is white.
	var white: Color = GameDB.club_colours(code)[2]
	if white.is_equal_approx(Color.WHITE) and UiKit.colour_distance(base, white) > 25.0:
		var w1: Dictionary = kit.duplicate()
		w1["base"] = white
		w1["pattern"] = base
		w1.erase("ring")
		out.append(w1)
		var w2: Dictionary = kit.duplicate()
		w2["base"] = white
		w2["pattern"] = pat
		w2.erase("ring")
		out.append(w2)
	var ring = kit.get("ring", null)
	if ring != null:
		var third: Dictionary = kit.duplicate()
		third["base"] = ring
		third["pattern"] = base
		third["ring"] = pat
		out.append(third)
		var third2: Dictionary = kit.duplicate()
		third2["base"] = ring
		third2["pattern"] = pat
		third2["ring"] = base
		out.append(third2)
	return out


## The third colour of a club that has one (Adelaide's gold, the Bulldogs'
## white) as a ring round the rim of the disc: it survives an 18 px disc, leaves
## the number clear, and is the one thing that tells Adelaide's navy and red
## from Melbourne's. `ring` is left out when it is the same as the body or the
## pattern (a ring that adds nothing).
static func with_trim(code: String, kit: Dictionary, keep := false) -> Dictionary:
	var out: Dictionary = kit.duplicate()
	if keep and out.has("ring"):
		return out
	out.erase("ring")
	if not GameDB.THREE_COLOUR_CLUBS.has(code):
		return out
	var third: Color = kit.get("pattern2", Color.WHITE)
	if UiKit.colour_distance(third, kit.get("base", Color.WHITE)) < 25.0:
		return out
	if UiKit.colour_distance(third, kit.get("pattern", Color.WHITE)) < 12.0 and str(kit.get("design", "plain")) != "plain":
		return out
	out["ring"] = third
	return out


## What a disc looks like, as colours sampled over its face (a 13 x 13 grid
## inside the circle, the kit's own geometry from _draw_kit).
static func disc_samples(kit: Dictionary) -> Array:
	var out := []
	var n := 13
	for iy in range(n):
		for ix in range(n):
			var x := (float(ix) + 0.5) / float(n) * 2.0 - 1.0
			var y := (float(iy) + 0.5) / float(n) * 2.0 - 1.0
			if x * x + y * y <= 1.0:
				out.append(kit_colour_at(kit, x, y))
	return out


## The designs clubs wore in earlier seasons, drawn on a disc as the nearest of
## the disc's shapes: a top half, a band, two hoops or a side.
const DISC_FAMILY := {"anchor": "yoke", "power97": "yoke", "swans90": "yoke", "saints97": "yoke",
		"lions10": "yoke", "eagles00": "panels", "giants12": "panels", "dogs90": "band",
		"dogs97": "band", "crows06": "lowhoops"}


## The disc shape a kit's design draws as.
static func disc_design(kit: Dictionary) -> String:
	var design := str(kit.get("design", "plain"))
	return str(DISC_FAMILY.get(design, design))


## The colour of the disc at (x, y) in the unit circle: the geometry _draw_kit
## draws.
static func kit_colour_at(kit: Dictionary, x: float, y: float) -> Color:
	var base: Color = kit.get("base", Color.WHITE)
	var pat: Color = kit.get("pattern", Color.DIM_GRAY)
	var ring = kit.get("ring", null)
	var design := disc_design(kit)
	var d := sqrt(x * x + y * y)
	var col := base
	if ring != null and d > 0.8:
		return ring
	var r := 0.94
	match design:
		"stripes":
			for cx in [-0.55, 0.0, 0.55]:
				if absf(x - float(cx) * r) < r * 0.13:
					col = pat
		"hoops", "lowhoops", "twohoops", "tiers":
			for cy in [-0.4, 0.3]:
				if absf(y - float(cy) * r) < r * 0.15:
					col = pat
		"sash":
			if absf(x) < r * 0.75 and y - x > -r * 0.42 and y - x < r * 0.42:
				col = pat
		"yoke", "shoulders":
			if y < -0.05 * r:
				col = pat
		"band":
			if absf(y) < r * 0.22:
				col = pat
		"chevron", "chevrons", "wings":
			if absf(x) < r * 0.7 and absf(y - (-0.35 + 0.75 * (1.0 - absf(x) / (r * 0.7))) * r) < r * 0.16:
				col = pat
		"panels", "sides", "giants", "map":
			if x < 0.0:
				col = pat
		_:
			if d < 0.55:
				col = pat
	return col


## The number's two inks on a kit: white with a dark edge, or (on a light body,
## Richmond's yellow) near-black with a white edge. Judged on the colours under
## the number (the middle of the disc).
static func number_inks(kit: Dictionary) -> Array:
	var lum := 0.0
	var cnt := 0
	for dy in [-0.3, 0.0, 0.3]:
		for dx in [-0.3, 0.0, 0.3]:
			var c := kit_colour_at(kit, float(dx), float(dy))
			lum += 0.2126 * c.srgb_to_linear().r + 0.7152 * c.srgb_to_linear().g + 0.0722 * c.srgb_to_linear().b
			cnt += 1
	if lum / float(cnt) > 0.30:
		return [Color(0.05, 0.05, 0.08), Color(1, 1, 1, 0.9)]
	return [Color(1, 1, 1), Color(0, 0, 0, 0.85)]


## How different two discs look on the turf, in CIELAB: half the distance
## between their palettes (each colour on one disc to the nearest colour on the
## other, by the share of the face it covers, both ways) and half the distance
## between their body colours. Layout does not count: Melbourne's red body and
## navy yoke against Adelaide's navy body and red hoops share their colours and
## score low; a third colour or a different body raises it.
static func disc_distance(a: Dictionary, b: Dictionary) -> float:
	var pa := _palette(a)
	var pb := _palette(b)
	var chamfer := 0.5 * (_palette_gap(pa, pb) + _palette_gap(pb, pa))
	return 0.5 * chamfer + 0.5 * UiKit.colour_distance(_dominant(_palette(_bodied(a))), _dominant(_palette(_bodied(b))))


## The colours on a disc and the share of its face each covers.
static func _palette(kit: Dictionary) -> Array:
	var counts := {}
	var cells := disc_samples(kit)
	for c in cells:
		var key := (c as Color).to_html(false)
		counts[key] = int(counts.get(key, 0)) + 1
	var out := []
	for key in counts:
		out.append([Color.html(str(key)), float(counts[key]) / float(cells.size())])
	return out


static func _palette_gap(from: Array, to: Array) -> float:
	var total := 0.0
	for f in from:
		var nearest := 1000.0
		for t in to:
			nearest = minf(nearest, UiKit.colour_distance(f[0], t[0]))
		total += nearest * float(f[1])
	return total


static func _bodied(kit: Dictionary) -> Dictionary:
	var k: Dictionary = kit.duplicate()
	k.erase("ring")
	return k


static func _dominant(p: Array) -> Color:
	var best: Array = p[0]
	for e in p:
		if float(e[1]) > float(best[1]):
			best = e
	return best[0]


## +1 when the home side kicks to the right of the screen, -1 when it kicks
## to the left: periods 1 and 3 one way, 2 and 4 the other.
static func end_sign(p: int) -> float:
	return 1.0 if p % 2 == 1 else -1.0


func _target_zoom() -> float:
	if not camera_enabled or director.tokens.is_empty() or events.is_empty():
		return 1.0
	return director.zoom_hint()


func _update_camera(delta: float) -> void:
	var tz := _target_zoom()
	var target := director.focus() if tz > 1.0 else Vector2.ZERO
	# Smooth follow in real time, a little quicker at high speed so the
	# camera keeps up with the play.
	var k := 1.0 - exp(-delta * 2.0 * clampf(sqrt(speed), 1.0, 2.5))
	_zoom = lerpf(_zoom, tz, 1.0 - exp(-delta * 1.4))
	_cam = _cam.lerp(target, k)
	_cam = _clamp_cam(_cam)


func _clamp_cam(c: Vector2) -> Vector2:
	var s := _scale()
	if s <= 0.0:
		return Vector2.ZERO
	var half := _flat_size() * 0.5 / s
	var lx := maxf(0.0, MatchMotion.HALF_LEN + 4.0 - half.x)
	var ly := maxf(0.0, MatchMotion.HALF_WID + 4.0 - half.y)
	return Vector2(clampf(c.x, -lx, lx), clampf(c.y, -ly, ly))


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
## The view's size with the ground lying flat (left to right): the control's own
## size, or that turned when the ground is upright.
func _flat_size() -> Vector2:
	return Vector2(size.y, size.x) if upright else size


## A point of the flat frame on the screen: itself, or turned a quarter turn
## about the view's centre (what was to the right is up).
func _to_screen(p: Vector2) -> Vector2:
	if not upright:
		return p
	var v := p - _flat_size() * 0.5
	return size * 0.5 + Vector2(v.y, -v.x)


## The rect the whole oval fills at zoom 1, with the ground lying flat.
func _flat_rect() -> Rect2:
	var fsz := _flat_size()
	var margin := 10.0
	var avail := fsz - Vector2(margin, margin) * 2.0
	if avail.x <= 0.0 or avail.y <= 0.0:
		return Rect2(Vector2.ZERO, fsz)
	var w := avail.x
	var h := w / ASPECT
	if h > avail.y:
		h = avail.y
		w = h * ASPECT
	return Rect2((fsz - Vector2(w, h)) * 0.5, Vector2(w, h))


## The rect the whole oval fills at zoom 1, on the screen.
func pitch_rect() -> Rect2:
	var r := _flat_rect()
	if not upright:
		return r
	var turned := Vector2(r.size.y, r.size.x)
	return Rect2((size - turned) * 0.5, turned)


## Pixels per metre at the current zoom.
func _scale() -> float:
	return _flat_rect().size.x / (2.0 * MatchMotion.HALF_LEN) * _zoom


## Ground metres to pixels on the screen.
func _w2s(p: Vector2) -> Vector2:
	if _oval3d != null and _vp3d != null:
		return _project3d(Vector3(p.x, 0.0, p.y))
	return _to_screen(_w2s_flat(p))


## Ground metres to pixels with the ground lying flat (the ground's own lines are
## drawn in this frame and turned as one).
func _w2s_flat(p: Vector2) -> Vector2:
	var m := end_sign(period)
	return _flat_size() * 0.5 + Vector2((p.x - _cam.x) * m, p.y - _cam.y) * _scale()


func _ellipse_points(c: Vector2, a: float, b: float, n: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(n + 1):
		var t := TAU * float(i) / float(n)
		pts.append(c + Vector2(cos(t) * a, sin(t) * b))
	return pts


## A mown stripe clipped exactly to the oval: sample the ellipse's half-height
## across the stripe's x-range and build the polygon from that.
func _stripe(c: Vector2, a: float, b: float, x0: float, x1: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var steps := 10
	for i in range(steps + 1):
		var x := lerpf(x0, x1, float(i) / float(steps))
		var t := clampf((x - c.x) / a, -1.0, 1.0)
		var yh := b * sqrt(1.0 - t * t)
		pts.append(Vector2(x, c.y - yh))
	for i in range(steps + 1):
		var x2 := lerpf(x1, x0, float(i) / float(steps))
		var t2 := clampf((x2 - c.x) / a, -1.0, 1.0)
		var yh2 := b * sqrt(1.0 - t2 * t2)
		pts.append(Vector2(x2, c.y + yh2))
	return pts


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
func _draw() -> void:
	if _oval3d != null:
		_draw_3d()
		return
	if _shake > 0.0:
		# Fades out as it ends; timed by the shake itself so a recording shows it as played.
		draw_set_transform(shake_offset())
	var r := pitch_rect()
	if r.size.x < 8.0 or r.size.y < 8.0:
		return
	_drawn_cam = _cam
	_drawn_zoom = _zoom
	var s := _scale()
	var c := _w2s_flat(Vector2.ZERO)
	var a := MatchMotion.HALF_LEN * s
	var b := MatchMotion.HALF_WID * s

	# The ground itself (stands, turf, lines, posts) is drawn lying flat and,
	# upright, turned as one piece: a quarter turn about the view's centre.
	var jolt := shake_offset() if _shake > 0.0 else Vector2.ZERO
	var base := Transform2D(Vector2(0, -1), Vector2(1, 0), Vector2(0, size.y) + jolt) if upright \
			else Transform2D(0.0, jolt)
	draw_set_transform_matrix(base)
	# The stadium round the fence, the replay's own seen from straight above: the
	# crowd in its seats in both clubs' colours, the fascia, the roof's edge, the
	# light towers (OvalStadium; built once a match, drawn as a few meshes).
	var weather := str(result.get("weather", ""))
	var tod := time_of_day(weather)
	var colours := _club_colours()
	var flat := _flat_size()
	_stadium.draw_stands(self, Rect2(-flat, flat * 3.0), c, s, colours, weather, tod)
	var fence := maxf(3.0, 2.0 * s)
	draw_colored_polygon(_ellipse_points(c, a + fence, b + fence, 128), FENCE_COLOUR)

	# Turf + mown stripes, the replay's grass as the day's weather leaves it, and
	# the light over it: brighter in the middle, darker toward the fence.
	_stadium.draw_turf(self, c, s, weather, tod, _light_texture())
	_stadium.draw_pools(self, c, s, tod)
	drawn_layers = ["turf"]
	_draw_press_zone(c, a, b)
	drawn_layers.append("press")
	# The coach's call marked on the grass, under the lines and the players.
	if _draw_marks(token_radius()) > 0:
		drawn_layers.append("marks")
	# The turf's edge in the stand's shadow: a few soft rings fading inward.
	var shade := maxf(6.0, 7.0 * s)
	for i in range(4):
		var inset := shade * float(i) / 4.0
		draw_polyline(_ellipse_points(c, a - inset, b - inset, 96),
				Color(0, 0, 0, 0.16 - 0.035 * float(i)), shade / 4.0 + 1.0, antialias)

	# Boundary
	draw_polyline(_ellipse_points(c, a, b, 128), Color(1, 1, 1, 0.85), 2.5, antialias)

	var line_col := Color(1, 1, 1, 0.55)
	var lw := 1.6

	# Centre square (50m) and centre circle (10m across)
	var sq := 25.0 * s
	draw_rect(Rect2(c - Vector2(sq, sq), Vector2(sq, sq) * 2.0), line_col, false, lw, antialias)
	draw_arc(c, 5.0 * s, 0, TAU, 32, line_col, lw, antialias)

	# 50m arcs and goal squares at each end
	var fifty_fs := fifty_font_size(s)
	var fifty := UiKit.BOLD.get_string_size("50", HORIZONTAL_ALIGNMENT_LEFT, -1, fifty_fs)
	var fifties: Array[Vector2] = []
	for sgn in [-1.0, 1.0]:
		var goal := _w2s_flat(Vector2(sgn * GOAL_LINE_M, 0.0))
		var rad := 50.0 * s
		var span := _arc_span(c, a, b, goal, rad)
		# The goal square a side kicks to wears that side's colour (director,
		# 2026-11-11: "need to make it more obvious somehow which end your team is
		# kicking toward"; "the arc being coloured too is too much, the goal square
		# is enough"). The ground's lines are drawn in the frame that mirrors at
		# each change of ends, so the colours change ends with the sides.
		var end_col := end_colour(_kits[0 if sgn > 0.0 else 1]) if _kits.size() == 2 else line_col
		var end_lw := lw if _kits.size() != 2 else END_LINE_W
		# A painted 50 sits on each arc near both boundary ends, the line broken
		# around it, as on a real ground (director, 2026-11-11: "the 50 metre arcs
		# should also have the number 50 in them"; "each arc neds 2 near the
		# boundary line sort of"). The numbers are drawn once the ground's turn is
		# undone, so they read level on a phone.
		var half := (maxf(fifty.x, fifty.y) * 0.5 + FIFTY_GAP) / rad
		var inset := minf(FIFTY_FROM_BOUNDARY_M / 50.0, (span.y - span.x) * 0.25)
		var lo := span.x + inset
		var hi := span.y - inset
		draw_arc(goal, rad, span.x, lo - half, 8, line_col, lw, antialias)
		draw_arc(goal, rad, lo + half, hi - half, 40, line_col, lw, antialias)
		draw_arc(goal, rad, hi + half, span.y, 8, line_col, lw, antialias)
		for ang in [lo, hi]:
			fifties.append(goal + Vector2(cos(ang), sin(ang)) * rad)
		# Goal square: 9m deep, 6.4m wide across the goal line.
		var depth := 9.0 * s
		var width := 6.4 * s
		var gx := goal.x - depth if goal.x > c.x else goal.x
		var square := Rect2(Vector2(gx, goal.y - width * 0.5), Vector2(depth, width))
		if _kits.size() == 2:
			draw_rect(square, Color(end_col, END_FILL_ALPHA))
		draw_rect(square, end_col, false, end_lw, antialias)
		# Goal posts 6.4m apart, behind posts a further 6.4m out.
		for py in [-1.0, 1.0]:
			draw_circle(goal + Vector2(0, py * 3.2 * s), maxf(2.0, 0.55 * s), Color(1, 1, 1, 0.95))
			draw_circle(goal + Vector2(0, py * 9.6 * s), maxf(1.5, 0.4 * s), Color(1, 1, 1, 0.7))

	# In the wind, the flags on the roof stream toward the end the breeze favours
	# (not lines over the grass: director, 2026-11-12).
	var now := float(Time.get_ticks_msec()) / 1000.0
	var windy := weather == VignetteWeather.WINDY
	stadium_drawn = {"time": tod, "flags": _stadium.flag_spots().size() if windy else 0, "toward": breeze_toward()}
	if windy:
		_stadium.draw_flags(self, base, c, s, colours, now, breeze_toward())
	draw_set_transform(jolt)
	for at in fifties:
		var mid := _to_screen(at)
		var origin := mid + Vector2(-fifty.x * 0.5, UiKit.BOLD.get_ascent(fifty_fs) * 0.5 - UiKit.BOLD.get_descent(fifty_fs) * 0.5)
		draw_string(UiKit.BOLD, origin, "50", HORIZONTAL_ALIGNMENT_LEFT, -1, fifty_fs, Color(1, 1, 1, 0.8))
	# Rain falls over the ground, under the players and the ball.
	VignetteWeather.draw_air(self, r, now, weather)
	var tr := token_radius()
	_layout_discs(tr)
	drawn_layers.append("discs")
	_draw_tokens(tr)
	_draw_rings(tr)
	if _figs != null:
		_figs.slots = _figure_slots(tr) if mini_figures else []
		_figs.queue_redraw()

	# Actor highlight
	var act := director.actor
	if act >= 0 and act < director.tokens.size():
		var p := _disc_at(act)
		draw_arc(p, disc_radius(act) * 1.9, 0, TAU, 28, Color(1, 1, 0.55, 0.95), 2.0, antialias)

	_draw_ball(tr, s)

	# Goal / behind flash
	var fl := director.flash
	if not fl.is_empty():
		var t := 1.0 - clampf(float(fl["left"]) / 0.9, 0.0, 1.0)
		var rad2 := lerpf(tr, minf(a, b) * 0.42, t)
		var col := Color(1.0, 0.92, 0.35) if fl["goal"] else Color(0.85, 0.9, 1.0)
		col.a = (1.0 - t) * 0.85
		var at := _w2s(fl["pos"])
		rad2 = minf(rad2, flash_room(at, tr))
		draw_arc(at, rad2, 0, TAU, 48, col, 4.0, antialias)
	_draw_role_labels(tr)
	_draw_caption(tr)
	_draw_press_banner()
	_draw_tip()


## The press zone: a wash of the press club's own colour over the part of the
## ground it is hunting, under the lines, the players and the ball. Its
## strength is the sim's own zone table (MatchDirector.press_zone_field,
## soft-edged); it eases in and out over PRESS_FADE_SECS of real time; the
## oval's edge is untouched. At the full strength of the opponents' back
## third it has to read on a phone without the unpressed ground beside it
## (director, 2026-10-13: the first 0.12 moved a channel by 8-11 of 255 and
## read as a darker turf stripe), so it was a 40% mix of the colour; the
## director then judged that too heavy ("right colour, about half as strong"),
## so the grass and its mowing stripes now show through. Half (0.2) was tried
## and lost the colours: through the green only the strength is halved, the hue
## goes slate (Fremantle), teal (Bulldogs, Melbourne, Carlton) and olive (St
## Kilda, Hawthorn). 0.3 is the least that still reads as each club's colour.
const PRESS_ZONE_ALPHA := 0.3
## The strength the colour is worked out at (what the club colour would be at
## a 40% mix), so the colour is the same hue and the strength the one above.
const PRESS_COLOUR_ALPHA := 0.4
const PRESS_FADE_SECS := 2.5
var _zone_fade := [0.0, 0.0]
var _press_said := [false, false]
var _caption_rect = null       # where the caption was drawn last (the press line steps clear of it)
var _press_banner := {}        # {text, left}: "<Club> push up to press."
var _ev_idx := 0
const PRESS_BANNER_SECS := 3.5


## The wash eases (smoothstep) rather than moving linearly.
static func ease_fade(t: float) -> float:
	return smoothstep(0.0, 1.0, t)


func _step_zone_fade(delta: float) -> void:
	for side in [0, 1]:
		var target: float = director.press_zone_level(side)
		_zone_fade[side] = move_toward(float(_zone_fade[side]), target, delta / PRESS_FADE_SECS)


func _draw_press_zone(c: Vector2, a: float, b: float) -> void:
	for side in [0, 1]:
		var fade := ease_fade(float(_zone_fade[side]))
		if fade <= 0.003:
			continue
		var base := press_zone_colour(home_code if side == 0 else away_code)
		var dir := MatchDirector._dir(side)
		# Slices across the oval, each a quad with a colour at both ends, so the
		# strength varies smoothly with no seam and no snap to a turf stripe.
		var n := 56
		var lo := -MatchMotion.HALF_LEN
		var hi := MatchMotion.HALF_LEN
		for i in range(n):
			var wx0 := lerpf(lo, hi, float(i) / float(n))
			var wx1 := lerpf(lo, hi, float(i + 1) / float(n))
			var k0 := MatchDirector.press_zone_field(wx0 * dir)
			var k1 := MatchDirector.press_zone_field(wx1 * dir)
			if k0 <= 0.002 and k1 <= 0.002:
				continue
			var x0 := _w2s_flat(Vector2(wx0, 0.0)).x
			var x1 := _w2s_flat(Vector2(wx1, 0.0)).x
			var xl := minf(x0, x1)
			var xr := maxf(x0, x1)
			var left_k := k0 if x0 <= x1 else k1
			var right_k := k1 if x0 <= x1 else k0
			var q := _stripe(c, a, b, xl, xr)
			var cols := PackedColorArray()
			for p in q:
				var t := 0.0 if xr <= xl else clampf((p.x - xl) / (xr - xl), 0.0, 1.0)
				cols.append(Color(base.r, base.g, base.b, PRESS_ZONE_ALPHA * fade * lerpf(left_k, right_k, t)))
			draw_polygon(q, cols)


## The oval marks the call (P-12 pass 5, director 2026-10-18: "Merge, then mark
## the oval"): Attack Corridor and Win Contest get a faint marking on the grass
## in the side's colour (press_zone_colour), so the call reads where the discs
## crowding the ball cannot say it. MatchDirector says when (corridor_mark_on,
## contest_mark); this draws, under the lines, the players and the ball, and
## moves nobody.
## - The corridor: the lanes' width plus a disc, from the side's defensive 50 to
##   the goal square, soft at its edges and ends, while the side has the ball.
## - The contest ring: round a ball-up or throw-in, the pack's ring planted on
##   the contest from the call to the clearance; in open play the midfield's ring
##   on the ball while it moves at a player's pace, easing out when the ball goes
##   faster than a sprint and back in where it comes down. The players on the ring stand
##   on its radius, so on a phone (a disc is 8.6 m across) a line there is under
##   their discs: the ring is drawn round the outside of them (radius plus a
##   disc), a faint pad of the colour inside, the rim at full strength.
## Strength: the press wash's faint state (0.3 x a half), never more. Where the
## press wash lies, a marking only tops the wash up to that, never adds on top
## (lead, 2026-10-18: the press tint stays as the director accepted it; under a
## full-strength hunting press the marking gives way). In and out over
## MARK_FADE_SECS of real time, eased: it never pops.
const MARK_ALPHA := PRESS_ZONE_ALPHA * MatchDirector.PRESS_ZONE_STANDING
const MARK_FADE_SECS := 0.5
const MARK_SIDE_FEATHER := 2.5     # metres: the corridor's long edges, soft
const MARK_END_FEATHER := 8.0      # ...and its ends, softer
const MARK_RIM := 2.0              # metres: the ring's rim, inside its edge...
const MARK_RIM_FEATHER := 1.5      # ...and its soft outer edge
const MARK_PAD := 0.5              # the pad inside the rim, this share of the rim's strength
const MARK_RIM_SAT := 0.4          # the rim's tint of the club colour (mark_rim_colour)
const MARK_OPEN_SHARE := 1.0       # ...as strong (0.7 did not show on a phone at 1x)
## The open-play ring's least time on (motion critic, 2026-10-18: a pad blinked on
## for five frames round a mark taken just before a set shot). The ring comes in
## only once the ball has been at a player's pace in open play this long (match
## seconds at 1x: a quarter of that in real time at 4x), so a shorter touch gets no
## pad; and once it shows it stays (easing out where it is) at least this long in
## real seconds, at every speed.
const MARK_OPEN_LEAST := 0.4
var _corr_fade := [0.0, 0.0]
var _stop_fade := [0.0, 0.0]
var _open_fade := [0.0, 0.0]
var _stop_ring := [{}, {}]         # {at, r}: the last stoppage ring, kept while it fades
var _open_ring := [{}, {}]
var _open_leaving := [false, false]   # the open ring easing out after a fast ball
var _open_wait := [0.0, 0.0]       # match seconds (at 1x) the ball has been at a player's pace in open play
var _open_on := [0.0, 0.0]         # real seconds the open ring has been showing
var _stop_on := [0.0, 0.0]         # real seconds the stoppage ring has been showing
var _mark_ball := Vector2.INF      # where the ball was last frame (its speed)
## The layers in the order the last frame drew them (tests: a marking under the discs).
var drawn_layers: Array = []


func _step_marks(delta: float) -> void:
	var md := delta * speed * MatchDirector.TEMPO if playing else 0.0
	var k := delta / MARK_FADE_SECS
	# The ball's speed this frame: faster than a sprint is a kick or handball in
	# flight (no player runs that fast: MatchMotion caps them at a sprint).
	var bpos: Vector2 = director.ball.get("pos", Vector2.ZERO) if not director.ball.is_empty() else Vector2.ZERO
	var fast := md > 0.0 and _mark_ball.is_finite() and bpos.distance_to(_mark_ball) > MatchMotion.SPRINT * md + 0.001
	_mark_ball = bpos
	for side in [0, 1]:
		_corr_fade[side] = move_toward(float(_corr_fade[side]), 1.0 if director.corridor_mark_on(side) else 0.0, k)
		var m: Dictionary = director.contest_mark(side)
		var stop := not m.is_empty() and bool(m["stop"])
		var open := not m.is_empty() and not bool(m["stop"])
		# The stoppage ring is planted on the contest from the call to the
		# clearance. A new contest elsewhere while it still shows: the old ring
		# goes out first, then the new one comes in on its own spot. It never slides.
		var sr: Dictionary = _stop_ring[side]
		if stop and not sr.is_empty() and float(_stop_fade[side]) > 0.0 				and (sr["at"] as Vector2).distance_to(m["at"]) > 0.01:
			stop = false
		elif stop:
			_stop_ring[side] = {"at": m["at"], "r": m["r"]}
		# The open-play ring is on the ball while the ball moves at a player's
		# pace. When it goes faster than a sprint (a kick or handball in flight)
		# the ring stays where it was and eases out, and eases back in where the
		# ball comes down: nothing drags across the ground.
		var on_ball := false
		_open_wait[side] = float(_open_wait[side]) + delta * speed if open and not fast else 0.0
		if open:
			var orr: Dictionary = _open_ring[side]
			if float(_open_fade[side]) <= 0.0:
				# A new ring only once the touch has lasted MARK_OPEN_LEAST.
				if float(_open_wait[side]) >= MARK_OPEN_LEAST - 0.0001:
					_open_ring[side] = {"at": bpos, "r": m["r"]}
					_open_leaving[side] = false
					on_ball = true
			elif fast:
				_open_leaving[side] = true
			elif bool(_open_leaving[side]):
				# Come down inside the ring (a short handball): it carries on.
				if (orr["at"] as Vector2).distance_to(bpos) <= mark_pad_radius(float(m["r"])) - mark_ball_radius():
					_open_leaving[side] = false
					on_ball = true
			else:
				on_ball = true
			if on_ball and float(_open_fade[side]) > 0.0:
				orr["at"] = (orr["at"] as Vector2).move_toward(bpos, MatchMotion.SPRINT * md)
				orr["r"] = m["r"]
		# Off the ball for any reason (a fast ball, or the ball out of open play):
		# planted where it is, easing out.
		if not on_ball and float(_open_fade[side]) > 0.0:
			_open_leaving[side] = true
		# A ball-up cleared in a frame or two (often at 4x) still shows its ring
		# MARK_OPEN_LEAST in all, easing out where it was planted: never a blink.
		var sf := float(_stop_fade[side])
		if stop or sf <= 0.0:
			_stop_fade[side] = move_toward(sf, 1.0 if stop else 0.0, k)
		else:
			var stop_left := MARK_OPEN_LEAST - float(_stop_on[side])
			_stop_fade[side] = move_toward(sf, 0.0, minf(k, sf * delta / stop_left) if stop_left > delta else k)
		_stop_on[side] = float(_stop_on[side]) + delta if float(_stop_fade[side]) > 0.0 else 0.0
		var of := float(_open_fade[side])
		if on_ball or of <= 0.0:
			_open_fade[side] = move_toward(of, 1.0 if on_ball else 0.0, k)
		else:
			# Easing out: never gone before it has shown MARK_OPEN_LEAST in all.
			var left := MARK_OPEN_LEAST - float(_open_on[side])
			_open_fade[side] = move_toward(of, 0.0, minf(k, of * delta / left) if left > delta else k)
		_open_on[side] = float(_open_on[side]) + delta if float(_open_fade[side]) > 0.0 else 0.0


## The ring's pad, its radius in metres: inside the rim (the ring's edge, `r` plus a disc).
func mark_pad_radius(r: float) -> float:
	var s := _scale()
	return r + (token_radius() / s if s > 0.0 else 0.0) - MARK_RIM


## The ball's drawn radius on the turf, in metres (_draw_ball: 0.42 of a disc).
func mark_ball_radius() -> float:
	var s := _scale()
	return 0.42 * token_radius() / s if s > 0.0 else 0.0


## Whether the open-play ring is off the ball, planted and easing out (after a ball
## faster than a sprint, or with the ball out of open play).
func open_ring_leaving(side: int) -> bool:
	return bool(_open_leaving[side])


## Whether any marking is showing or fading (the view keeps redrawing).
func marks_live() -> bool:
	for side in [0, 1]:
		if float(_corr_fade[side]) > 0.0 or float(_stop_fade[side]) > 0.0 or float(_open_fade[side]) > 0.0:
			return true
	return false


## Each marking's strength now, for the tests: {"corridor": [a0, a1], "stop": [...],
## "open": [...]}, the alpha it is laid at before the press wash takes its share.
func mark_alphas() -> Dictionary:
	var out := {"corridor": [], "stop": [], "open": []}
	for side in [0, 1]:
		(out["corridor"] as Array).append(MARK_ALPHA * ease_fade(float(_corr_fade[side])))
		(out["stop"] as Array).append(MARK_ALPHA * ease_fade(float(_stop_fade[side])))
		(out["open"] as Array).append(MARK_ALPHA * MARK_OPEN_SHARE * ease_fade(float(_open_fade[side])))
	return out


## The press wash's strength at `wx` metres (the director's frame): the most of
## either side's, as _draw_press_zone lays it.
func press_alpha_at(wx: float) -> float:
	var out := 0.0
	for side in [0, 1]:
		var f := ease_fade(float(_zone_fade[side]))
		if f > 0.003:
			out = maxf(out, PRESS_ZONE_ALPHA * f * MatchDirector.press_zone_field(wx * MatchDirector._dir(side)))
	return out


## A marking's alpha at a point where it wants `want`: only what tops the press
## wash up to it, never more on top.
func mark_over_press(want: float, wx: float) -> float:
	return maxf(0.0, want - press_alpha_at(wx))


## Draws every marking showing; returns how many it drew.
func _draw_marks(tr: float) -> int:
	var s := _scale()
	if s <= 0.0:
		return 0
	var drew := 0
	var disc_m := BODY3D_CLEAR if _oval3d != null else tr / s
	for side in [0, 1]:
		var code := home_code if side == 0 else away_code
		var base := press_zone_colour(code)
		var rim := mark_rim_colour(code)
		var cf := MARK_ALPHA * ease_fade(float(_corr_fade[side]))
		if cf > 0.002:
			_draw_corridor(side, base, cf, MatchDirector.CORRIDOR_HALF + disc_m)
			drew += 1
		var sf := MARK_ALPHA * ease_fade(float(_stop_fade[side]))
		if sf > 0.002 and not (_stop_ring[side] as Dictionary).is_empty():
			var sr: Dictionary = _stop_ring[side]
			_draw_mark_ring(sr["at"], float(sr["r"]) + disc_m, base, rim, sf)
			drew += 1
		var of := MARK_ALPHA * MARK_OPEN_SHARE * ease_fade(float(_open_fade[side]))
		if of > 0.002 and not (_open_ring[side] as Dictionary).is_empty():
			var orr: Dictionary = _open_ring[side]
			_draw_mark_ring(orr["at"], float(orr["r"]) + disc_m, base, rim, of)
			drew += 1
	return drew


## The corridor shade: slices up the ground, each a strip of quads across it with
## a colour at every corner, soft at the edges.
func _draw_corridor(side: int, base: Color, a: float, half: float) -> void:
	var dir := MatchDirector._dir(side)
	# Full strength over the whole corridor; the soft ends lie outside it.
	var x0 := MatchDirector.CORRIDOR_FROM - MARK_END_FEATHER
	var x1 := MatchDirector.CORRIDOR_TO + MARK_END_FEATHER
	var ys := [-half - MARK_SIDE_FEATHER, -half, half, half + MARK_SIDE_FEATHER]
	var yk := [0.0, 1.0, 1.0, 0.0]
	var n := 24
	for i in range(n):
		var xa := lerpf(x0, x1, float(i) / float(n))
		var xb := lerpf(x0, x1, float(i + 1) / float(n))
		var ka := corridor_end(xa)
		var kb := corridor_end(xb)
		for j in range(3):
			var pts := [Vector2(xa * dir, ys[j]), Vector2(xb * dir, ys[j]),
					Vector2(xb * dir, ys[j + 1]), Vector2(xa * dir, ys[j + 1])]
			var ks := [ka * float(yk[j]), kb * float(yk[j]), kb * float(yk[j + 1]), ka * float(yk[j + 1])]
			var xs := [xa, xb, xb, xa]
			var cols := PackedColorArray()
			var any := false
			for q in range(4):
				var al := mark_over_press(a * float(ks[q]), float(xs[q]) * dir)
				any = any or al > 0.001
				cols.append(Color(base.r, base.g, base.b, al))
			if any:
				_ground_polygon(pts, cols)


## The corridor's strength along the ground (metres up it from the centre, for
## its own side): full from the defensive 50 to the goal square, easing to
## nothing over MARK_END_FEATHER beyond each end (lead's check, 2026-10-18: with
## the ease inside, the shade only read from the centre square).
static func corridor_end(x: float) -> float:
	var x0 := MatchDirector.CORRIDOR_FROM
	var x1 := MatchDirector.CORRIDOR_TO
	return smoothstep(x0 - MARK_END_FEATHER, x0, x) * (1.0 - smoothstep(x1, x1 + MARK_END_FEATHER, x))


## The ring's rim: a light tint of the club's colour, so a line a few pixels wide
## reads on the dark turf at the same faint strength (the wash's colour, worked to
## mix at turf lightness, only darkens the grass in a line that thin). A club with
## no hue gets a light grey.
static func mark_rim_colour(code: String) -> Color:
	var base := press_zone_colour(code)
	if base == PRESS_NO_HUE:
		return Color(0.85, 0.85, 0.85)
	return Color.from_hsv(base.h, MARK_RIM_SAT, 1.0)


## A ring on the grass round `at` (metres), its edge at `edge`: the rim (in `rim`)
## at `a` just inside the edge, soft to nothing just outside it, a pad of `base`
## at MARK_PAD of it within.
func _draw_mark_ring(at: Vector2, edge: float, base: Color, rim: Color, a: float) -> void:
	var rs := [0.0, edge - MARK_RIM, edge - MARK_RIM * 0.3, edge, edge + MARK_RIM_FEATHER]
	var rk := [MARK_PAD, MARK_PAD, 1.0, 1.0, 0.0]
	var n := 56
	for i in range(n):
		var t0 := TAU * float(i) / float(n)
		var t1 := TAU * float(i + 1) / float(n)
		for j in range(rs.size() - 1):
			var w := [at + Vector2.from_angle(t0) * float(rs[j]), at + Vector2.from_angle(t1) * float(rs[j]),
					at + Vector2.from_angle(t1) * float(rs[j + 1]), at + Vector2.from_angle(t0) * float(rs[j + 1])]
			var ks := [rk[j], rk[j], rk[j + 1], rk[j + 1]]
			if j == 0:
				# The middle: a triangle from the centre, not a quad with two corners on it.
				w.remove_at(1)
				ks.remove_at(1)
			var cols := PackedColorArray()
			var any := false
			for q in range(w.size()):
				var wp: Vector2 = w[q]
				var al := mark_over_press(a * float(ks[q]), wp.x)
				any = any or al > 0.001
				var c: Color = base if float(ks[q]) <= MARK_PAD + 0.001 else rim
				cols.append(Color(c.r, c.g, c.b, al))
			if any:
				_ground_polygon(w, cols)


## The turf the wash sits on, for working out what colour to lay over it.
const PRESS_TURF := Color(0.118, 0.333, 0.133)
## Which of a club's colours it is known by, as UiKit.club_ink chooses it
## (INK_SLOT on claude/break-best-so-far, PR #666): the first, except the
## Bulldogs and Essendon, whose second is the one a supporter names; -1 is a
## club with no hue (Collingwood). Kept here so the two can be unified once
## #666 is on main; this file does not touch UiKit.
const PRESS_INK_SLOT := {"WBD": 1, "ESS": 1, "COL": -1}
## What the wash should look like once mixed with the turf: the club's hue,
## saturated, at about the turf's own lightness, so the grass is still grass
## and the colour still the club's.
const PRESS_TARGET_V := 0.64
## A club with no hue (Collingwood, or a custom club in black and white): a
## dark, cool wash, the zone's shape carrying the rest.
const PRESS_NO_HUE := Color(0.02, 0.03, 0.07)


## The colour to lay over the turf at PRESS_COLOUR_ALPHA so the mix lands on the
## club's colour at turf lightness: the plain colour of a dark club (navy,
## brown, deep purple) would only darken the grass, and a plain blue or red
## drifts to teal or brown through the green beneath it. Worked back from the
## mix, kept in range.
static func press_zone_colour(code: String) -> Color:
	var cols: Array = GameDB.club_colours(code)
	var slot := int(PRESS_INK_SLOT.get(code, 0))
	if slot < 0:
		return PRESS_NO_HUE
	var pick: Color = cols[slot]
	if pick.s < 0.25:
		# A custom club whose first colour is black or white: its most saturated.
		pick = Color(0, 0, 0, 0)
		var best := 0.25
		for c in cols:
			var col: Color = c
			if col.s > best:
				best = col.s
				pick = col
		if pick.a == 0.0:
			return PRESS_NO_HUE
	var target := Color.from_hsv(pick.h, clampf(pick.s, 0.6, 0.85), PRESS_TARGET_V)
	var w := (Vector3(target.r, target.g, target.b) - Vector3(PRESS_TURF.r, PRESS_TURF.g, PRESS_TURF.b) * (1.0 - PRESS_COLOUR_ALPHA)) / PRESS_COLOUR_ALPHA
	return Color(clampf(w.x, 0.0, 1.0), clampf(w.y, 0.0, 1.0), clampf(w.z, 0.0, 1.0))


## A thin light ring on each of your players with a call on him or a run
## promised. Quieter than the actor's ring, which stays the one that moves.
func _draw_rings(tr: float) -> void:
	if rings.is_empty():
		return
	for t in director.tokens:
		if float(t["down"]) > 0.0 or not rings.has(str(t.get("pid", ""))):
			continue
		var p := _disc_at(int(t["id"]))
		if p.x < -tr * 3.0 or p.y < -tr * 3.0 or p.x > size.x + tr * 3.0 or p.y > size.y + tr * 3.0:
			continue
		draw_arc(p, disc_radius(int(t["id"])) * 1.5, 0, TAU, 28, Color(RING_COLOUR, 0.9), 1.6, antialias)


## The name over a player, in the type the team shape uses: bold, outlined so it
## reads on the turf, never smaller than a phone can read, and kept inside the
## view.
## The players with a recorded job (MatchDirector.role_labels) carry their
## surname under the token, small and quiet, so the viewer can follow the
## tagger, the loose man and his minder without a coaching overlay. The
## passing caption (a goal, a ringed player's touch) still sits above.
func _draw_role_labels(tr: float) -> void:
	var fs := role_label_size(tr)
	for l in role_label_layout(tr, fs):
		var text := str(l["text"])
		var origin: Vector2 = l["origin"]
		for off in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]:
			draw_string(UiKit.BOLD, origin + off, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0, 0, 0, 0.7))
		draw_string(UiKit.BOLD, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1, 1, 1, 0.85))


## The surnames' size: never under the 13 px floor (row T3.R9), and a little
## bigger under the bigger discs of a PC, where there is room for it.
static func role_label_size(tr: float) -> int:
	return clampi(int(tr * 0.85), UiKit.FINE, 16)


## The jumper number's size on a disc of radius tr: it grows and shrinks with the
## disc, and is never under the 13 px floor (row T3.R9), which is what the
## smallest disc in a pack carries on a phone (14 px on a full one).
static func number_size(tr: float) -> int:
	return int(clampf(tr * 1.1, float(UiKit.FINE), NUMBER_MAX))


## Where each surname goes: [{id, text, origin, rect}]. Under its disc first;
## when that would sit on another name or on another player's disc (and its
## number) it moves to above, beside, or further below; a name with no clear
## place is left out, except the ball carrier's, which is always written (the
## nearest clear place, else under his disc).
func role_label_layout(tr: float, fs: int) -> Array:
	var named := label_wanted()
	var ids := named.keys()
	# The ball carrier first, then ringed players, then the rest, so the
	# important names claim their place before the others.
	ids.sort_custom(func(x, y): return int(named[x]) < int(named[y]) or (int(named[x]) == int(named[y]) and int(x) < int(y)))
	# A player whose name the caption is writing (a goal, a touch) is not named
	# twice.
	var captioned := int(_caption["tok"]) if not _caption.is_empty() else -1
	var discs := []
	for i in range(director.tokens.size()):
		discs.append(_disc_at(i))
	var placed := []
	var out := []
	var full := tr
	for id in ids:
		if id < 0 or id >= director.tokens.size() or int(id) == captioned:
			continue
		var t: Dictionary = director.tokens[id]
		if float(t.get("down", 0.0)) > 0.0:
			continue
		var text := str(t.get("surname", ""))
		if text == "":
			continue
		var width := UiKit.BOLD.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var p: Vector2 = discs[id]
		if p.x < -width or p.y < 0.0 or p.x > size.x + width or p.y > size.y + float(fs) * 2.0:
			continue
		var h := float(fs)
		# Beside the disc as it is drawn (smaller in a pack).
		tr = minf(full, disc_radius(id))
		# Only places beside the disc: under, over, either side (a name far
		# from its disc names the wrong player).
		var spots := [
			Vector2(-width * 0.5, tr * 1.25 + h),
			Vector2(-width * 0.5, -tr * 1.25 - 3.0),
			Vector2(tr * 1.3, h * 0.35),
			Vector2(-tr * 1.3 - width, h * 0.35),
			Vector2(tr * 1.0, tr * 1.1 + h * 0.8),
			Vector2(-tr * 1.0 - width, tr * 1.1 + h * 0.8),
			Vector2(tr * 1.0, -tr * 1.1),
			Vector2(-tr * 1.0 - width, -tr * 1.1),
		]
		var chosen = null
		# First a place clear of every name and every other disc; failing that,
		# one clear of the names (it may lie over a neighbour's edge, but the
		# name is still written beside its own disc).
		for strict in [true, false]:
			for off in spots:
				var origin: Vector2 = p + off
				origin.x = clampf(origin.x, 2.0, maxf(2.0, size.x - width - 2.0))
				var rect := Rect2(origin + Vector2(-1, -h), Vector2(width + 2.0, h + 3.0))
				if _label_clear(rect, id, placed, discs, full, strict):
					chosen = [origin, rect]
					break
			if chosen != null:
				break
		if chosen == null:
			continue
		placed.append(chosen[1])
		out.append({"id": id, "text": text, "origin": chosen[0], "rect": chosen[1]})
	return out


## The players whose name is wanted under the disc, with a priority (lower
## first): the ball carrier, your ringed players, those with a recorded job.
func label_wanted() -> Dictionary:
	var named := {}
	for id in director.role_labels():
		named[int(id)] = 1
	var holder := int(director.ball.get("holder", -1)) if not director.ball.is_empty() else -1
	if holder >= 0:
		named[holder] = -1
	if not rings.is_empty():
		for i in range(director.tokens.size()):
			if rings.has(str(director.tokens[i].get("pid", ""))):
				named[i] = mini(int(named.get(i, 0)), 0)
	return named


## A name's box clear of every name already placed and of every other player's
## disc (so no name runs over a number).
func _label_clear(rect: Rect2, id: int, placed: Array, discs: Array, tr: float, strict := true) -> bool:
	for r in placed:
		if rect.intersects(r as Rect2):
			return false
	if not strict:
		return true
	for i in range(discs.size()):
		if i == id or float(director.tokens[i].get("down", 0.0)) > 0.0:
			continue
		var c: Vector2 = discs[i]
		var nx := clampf(c.x, rect.position.x, rect.end.x)
		var ny := clampf(c.y, rect.position.y, rect.end.y)
		if Vector2(nx, ny).distance_to(c) < minf(tr, disc_radius(i)):
			return false
	return true


func _draw_press_banner() -> void:
	if _press_banner.is_empty():
		return
	var text := str(_press_banner["text"])
	var fs := 20
	var font := UiKit.BOLD
	var width := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var origin := Vector2(clampf((size.x - width) * 0.5, 4.0, maxf(4.0, size.x - width - 4.0)), float(fs) + 10.0)
	# Never over the "Turnover" / name caption: if they would meet, the line
	# steps below it.
	if _caption_rect != null:
		var mine := Rect2(origin - Vector2(4, float(fs)), Vector2(width + 8.0, float(fs) + 8.0))
		if mine.intersects(_caption_rect as Rect2):
			origin.y = (_caption_rect as Rect2).end.y + float(fs) + 6.0
	var fade := clampf(float(_press_banner["left"]) / 0.4, 0.0, 1.0)
	# Plain text with a soft dark shadow and an outline: no pill.
	for off in [Vector2(0, 2), Vector2(1, 2), Vector2(-1, 2)]:
		draw_string(font, origin + off, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0, 0, 0, 0.35 * fade))
	for off in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1), Vector2(-1, -1), Vector2(1, 1), Vector2(-1, 1), Vector2(1, -1)]:
		draw_string(font, origin + off, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(0, 0, 0, 0.8 * fade))
	draw_string(font, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(1, 1, 1, fade))


func _draw_caption(tr: float) -> void:
	_caption_rect = null
	if _caption.is_empty():
		return
	var tok := int(_caption["tok"])
	var text := str(_caption["text"])
	if text == "" or tok < 0 or tok >= director.tokens.size():
		return
	var turnover := bool(_caption.get("turnover", false))
	# A turnover is a cue, not a name: a size up, so it reads at a glance.
	var fs := clampi(int(tr * (2.1 if turnover else 1.6)), 15 if turnover else 11, 20 if turnover else 15)
	var width := UiKit.BOLD.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var p := _disc_at(tok)
	if not _caption_on_view(p):
		return
	var origin := caption_origin(p, width, fs, tr)
	_caption_rect = Rect2(origin - Vector2(4, float(fs)), Vector2(width + 8.0, float(fs) + 10.0))
	# It fades over its last third of a second.
	var fade := clampf(float(_caption["left"]) / 0.3, 0.0, 1.0)
	for off in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]:
		draw_string(UiKit.BOLD, origin + off, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs,
				Color(0, 0, 0, 0.8 * fade))
	draw_string(UiKit.BOLD, origin, text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color(RING_COLOUR, fade))
	if turnover:
		# Underlined in the winning club's colour: whose ball it is now, at a glance.
		var kit: Dictionary = _kits[clampi(int(_caption.get("side", 0)), 0, 1)]
		var bar: Color = kit.get("base", RING_COLOUR)
		# A light edge round the club bar so a dark kit colour still shows on the grass.
		draw_rect(Rect2(origin + Vector2(-2, 3), Vector2(width + 4, 6)), Color(RING_COLOUR, 0.85 * fade))
		draw_rect(Rect2(origin + Vector2(-1, 4), Vector2(width + 2, 4)), Color(bar, fade))


## Where a caption (a scorer's name, "Turnover") is written for the player at
## `p`: above him, and above every disc it would otherwise cover, with a clear
## gap, so the call never hides the players round the ball (lead, 2026-10-14). If
## the pack reaches the top of the view it goes below the pack instead. Returns
## the text's baseline origin; the caption's box is CAPTION_BOX_BELOW deeper
## (the underline) and its own height taller.
const CAPTION_GAP := 4.0
const CAPTION_BOX_BELOW := 10.0
func caption_origin(p: Vector2, width: float, fs: int, tr: float) -> Vector2:
	var x := clampf(p.x - width * 0.5, 4.0, maxf(4.0, size.x - width - 4.0))
	# In 3D a "disc" is half a body round his middle: just over his head is a lift of 1.2.
	var lift := 1.2 if _oval3d != null else 2.4
	var up := _caption_clear(Vector2(x, p.y - tr * lift), width, fs, tr, -1.0)
	if up.y >= float(fs) + 2.0:
		return up
	var down := _caption_clear(Vector2(x, p.y + tr * lift + float(fs)), width, fs, tr, 1.0)
	if down.y + CAPTION_BOX_BELOW <= size.y - 2.0:
		return down
	return Vector2(x, maxf(up.y, float(fs) + 2.0))


## Move a caption up (dir -1) or down (dir 1) until its box touches no disc.
func _caption_clear(origin: Vector2, width: float, fs: int, tr: float, dir: float) -> Vector2:
	for pass_no in range(12):
		var box := Rect2(origin.x - 4.0, origin.y - float(fs), width + 8.0, float(fs) + CAPTION_BOX_BELOW)
		var grown := box.grow(tr + CAPTION_GAP)
		var moved := false
		for d in _disc:
			if not grown.has_point(d):
				continue
			if dir < 0.0:
				origin.y = minf(origin.y, d.y - tr - CAPTION_GAP - CAPTION_BOX_BELOW - 0.5)
			else:
				origin.y = maxf(origin.y, d.y + tr + CAPTION_GAP + float(fs) + 0.5)
			moved = true
		if not moved:
			break
	return origin


## In 3D a caption is written only over a body on view: kept inside the view, the
## name of a man off it would sit over someone else (the feed still names him).
func _caption_on_view(p: Vector2) -> bool:
	return _oval3d == null or Rect2(Vector2.ZERO, size).has_point(p)


## The caption's box as it would be drawn now, or an empty rect: for tests.
func caption_box() -> Rect2:
	if _caption.is_empty():
		return Rect2()
	var tok := int(_caption["tok"])
	var text := str(_caption["text"])
	if text == "" or tok < 0 or tok >= director.tokens.size():
		return Rect2()
	var tr := token_radius()
	var turnover := bool(_caption.get("turnover", false))
	var fs := clampi(int(tr * (2.1 if turnover else 1.6)), 15 if turnover else 11, 20 if turnover else 15)
	var width := UiKit.BOLD.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	if not _caption_on_view(_disc_at(tok)):
		return Rect2()
	var origin := caption_origin(_disc_at(tok), width, fs, tr)
	return Rect2(origin - Vector2(4, float(fs)), Vector2(width + 8.0, float(fs) + CAPTION_BOX_BELOW))


func _draw_ball(tr: float, s: float) -> void:
	if director.ball.is_empty():
		return
	# A short trail on the turf, brightest at the ball, gone a moment later.
	if _trail.size() >= 2:
		for i in range(1, _trail.size()):
			var k := float(i) / float(_trail.size() - 1)
			draw_line(_w2s(_trail[i - 1]), _w2s(_trail[i]), Color(0.98, 0.93, 0.75, 0.55 * k),
					maxf(1.0, tr * 0.22 * k), antialias)
	var ground := ball_point()
	var h := float(director.ball["h"])
	# Shadow on the turf, the ball lifted by its height: a kick visibly climbs
	# and drops, a handball stays flat.
	var sh := 1.0 / (1.0 + h / 12.0)
	draw_colored_polygon(_ellipse_points(ground, tr * 0.42 * sh, tr * 0.24 * sh, 12),
			Color(0, 0, 0, 0.35 * sh))
	var lift := ground - Vector2(0, h * s * 0.55)
	var grow := 1.0 + h / 26.0
	draw_colored_polygon(_ellipse_points(lift, tr * 0.42 * grow, tr * 0.30 * grow, 12),
			Color(0.98, 0.93, 0.75))
	draw_polyline(_ellipse_points(lift, tr * 0.42 * grow, tr * 0.30 * grow, 12),
			Color(0.25, 0.12, 0.08), 1.0, antialias)


## How big the goal's ring may grow at `at` and stay in the view and off the
## bench's tab: upright, a goal is a few pixels from the top or bottom edge, and a
## ring sized for the ground ran off the screen.
func flash_room(at: Vector2, tr: float) -> float:
	var room := minf(minf(at.x, size.x - at.x), minf(at.y, size.y - at.y)) - 3.0
	var tab := bench_tab_rect()
	if tab.size.x > 0.0:
		var near := Vector2(clampf(at.x, tab.position.x, tab.end.x), clampf(at.y, tab.position.y, tab.end.y))
		room = minf(room, near.distance_to(at) - 6.0)
	return maxf(tr, room)


## The radius of a player's disc at its full size, in pixels: what a disc that
## overlaps no other is drawn at. disc_radius is what each one is drawn at now.
func token_radius() -> float:
	if _oval3d != null and _tr3d > 0.0:
		return _tr3d
	var r := pitch_rect()
	return maxf(TOKEN_MIN, minf(r.size.x, r.size.y) * 0.5 * DISC_SHARE * sqrt(_zoom))


## The smallest radius a disc is drawn at, in a pack: the old size.
func small_radius() -> float:
	if _oval3d != null and _tr3d > 0.0:
		return _tr3d
	var r := pitch_rect()
	return maxf(SMALL_MIN, minf(r.size.x, r.size.y) * 0.5 * SMALL_SHARE * sqrt(_zoom))


## The radius a disc is drawn toward when the second-nearest other player is
## `gap` px from his on the screen: PACK_FIT of the gap, between the small and the
## full size. The same for both sides.
static func pack_radius(gap: float, small: float, full: float) -> float:
	return clampf(gap * PACK_FIT, small, full)


## The radius token `id`'s disc is drawn at now, in pixels (the last layout's):
## the one size the drawing, the tap, the draw-apart, the rings and marks round
## a disc and the tests all read.
func disc_radius(id: int) -> float:
	if _oval3d != null and id >= 0 and id < _r3d.size():
		return _r3d[id]
	if id >= 0 and id < _disc_k.size():
		return lerpf(small_radius(), token_radius(), _disc_k[id])
	return token_radius()


## Where token `id` is drawn: his place on the ground, nudged clear of a disc
## he would overlap (_layout_discs).
func _disc_at(id: int) -> Vector2:
	if id >= 0 and id < _disc.size():
		return _disc[id]
	return _w2s(director.tokens[id]["pos"])


## Work out where every disc is drawn this frame. Two discs closer than a
## diameter are moved apart along the line between them, half each, until none
## overlap; the move is kept from frame to frame and eases away once the players
## part. The match's own positions are never touched.
func _layout_discs(tr: float) -> void:
	var n := director.tokens.size()
	if _nudge.size() != n or _disc_k.size() != n:
		_nudge.resize(n)
		_nudge.fill(Vector2.ZERO)
		_disc_k.resize(n)
		_disc_k.fill(1.0)
		_nudge_h = -1.0
	# How far a disc may be moved apart, or back, since the last layout.
	var budget := INF if nudge_full or _nudge_h < 0.0 else MatchMotion.WALK * _nudge_h * _scale()
	# How far a disc's size may change since the last layout (the first is at once).
	var resize := INF if _nudge_h < 0.0 else _nudge_h / RESIZE_SECS
	_nudge_h = 0.0
	var was := _nudge.duplicate()
	var real := PackedVector2Array()
	real.resize(n)
	var pos := PackedVector2Array()
	pos.resize(n)
	for i in range(n):
		real[i] = _w2s(director.tokens[i]["pos"])
		_nudge[i] *= NUDGE_EASE
		pos[i] = real[i] + _nudge[i]
	# Each disc's size, eased toward what the players round it leave room for.
	var small := small_radius()
	var rad := PackedFloat32Array()
	rad.resize(n)
	for i in range(n):
		var near := INF
		var next := INF
		for j in range(n):
			if j == i:
				continue
			var gap := real[i].distance_squared_to(real[j])
			if gap < near:
				next = near
				near = gap
			elif gap < next:
				next = gap
		var k := inverse_lerp(small, tr, pack_radius(sqrt(next), small, tr)) if tr > small else 1.0
		_disc_k[i] = k if resize == INF else move_toward(_disc_k[i], k, resize)
		rad[i] = lerpf(small, tr, _disc_k[i])
	# A disc is never drawn further from its player than it was at the old size.
	var cap := INF if nudge_full else small * 2.0 * NUDGE_CAP
	for pass_no in range(NUDGE_PASSES):
		var moved := false
		for i in range(n):
			for j in range(i + 1, n):
				var d := pos[j] - pos[i]
				var want := (rad[i] + rad[j]) * NUDGE_GAP
				if absf(d.x) >= want or absf(d.y) >= want:
					continue
				var dist := d.length()
				if dist >= want:
					continue
				# Two on the very same spot part along a line of their own, the
				# same one every frame.
				var dir := d / dist if dist > 0.01 else Vector2.RIGHT.rotated(float(i * 7 + j))
				var push := (want - dist) * 0.5 + 0.02
				pos[i] -= dir * push
				pos[j] += dir * push
				moved = true
		if not moved:
			break
		if cap < INF:
			for i in range(n):
				var off := pos[i] - real[i]
				if off.length() > cap:
					pos[i] = real[i] + off.limit_length(cap)
	for i in range(n):
		var off := pos[i] - real[i]
		if budget < INF:
			off = was[i] + (off - was[i]).limit_length(budget)
		if cap < INF:
			off = off.limit_length(cap)
		_nudge[i] = off
		pos[i] = real[i] + off
	_disc = pos


## The order the discs are drawn in, last on top: lower on the screen over
## higher, then the player id, and the man with the ball over everyone. The
## order is kept from frame to frame: two discs change places only once one has
## passed the other on screen by more than a disc's radius (the motion critic,
## 2026-10-18: discs swapping in front of each other as players neared the ball).
## Only the ball changing hands lifts a disc to the top at once.
var _order: Array = []


func draw_order() -> Array:
	var n := director.tokens.size()
	if _order.size() != n:
		_order = range(n)
		_order.sort_custom(func(a, b): return _disc_at(a).y < _disc_at(b).y \
				or (_disc_at(a).y == _disc_at(b).y and a < b))
	var ys := PackedFloat32Array()
	ys.resize(n)
	for i in range(n):
		ys[i] = _disc_at(i).y
	var r := token_radius()
	# Neighbours swap only when the one drawn first is lower by more than a
	# radius; every swap undoes one such crossing, so this always ends.
	var moved := true
	var guard := 0
	while moved and guard < n * n:
		moved = false
		for k in range(n - 1):
			guard += 1
			var a: int = _order[k]
			var b: int = _order[k + 1]
			if ys[a] > ys[b] + r:
				_order[k] = b
				_order[k + 1] = a
				moved = true
	var out := _order.duplicate()
	var carrier := top_disc()
	if carrier >= 0:
		out.erase(carrier)
		out.append(carrier)
	return out


## The player drawn on top of everyone: the man with the ball, or the last to
## have it while it is in the air; -1 for none.
func top_disc() -> int:
	var n := director.tokens.size()
	var carrier := int(director.ball.get("holder", -1))
	if carrier < 0 or carrier >= n:
		carrier = director.actor if director.actor >= 0 and director.actor < n else -1
	return carrier


## The player whose disc is drawn at `p` (a point in this view), -1 for none: the
## one drawn on top where discs overlap. For a tap on the oval.
func disc_at_point(p: Vector2) -> int:
	var order := draw_order()
	# On a disc: the one drawn on top there, at the size it is drawn.
	for k in range(order.size() - 1, -1, -1):
		var id := int(order[k])
		if _disc_at(id).distance_to(p) <= disc_radius(id):
			return id
	# Beside one: the nearest within a thumb's reach, which is a full disc and a
	# quarter whatever size the disc is drawn at (a small disc in a pack is no
	# harder to press than a full one).
	var reach := token_radius() * 1.25
	var best := -1
	for id2 in order:
		var dist := _disc_at(int(id2)).distance_to(p)
		if dist <= reach:
			reach = dist
			best = int(id2)
	return best


## Where the discs are drawn now, for tests and the capture tool: a layout
## step exactly as a drawn frame makes it.
func disc_positions() -> PackedVector2Array:
	_layout_discs(token_radius())
	return _disc


## Where the last drawn frame put the discs (no new layout step), for the
## capture tool's motion print.
func disc_positions_drawn() -> PackedVector2Array:
	return _disc


## The bench's drawer (its tab, its panel, what it lists).
func bench_drawer() -> BenchDrawer:
	return _bench


## The tab's pill on the view; an empty rect while there is no bench to open.
func bench_tab_rect() -> Rect2:
	if _bench == null or not _bench.has_bench():
		return Rect2()
	var t := _bench.tab()
	return Rect2(t.position + Vector2(0.0, t.size.y - BenchDrawer.TAB_PILL_H), Vector2(t.size.x, BenchDrawer.TAB_PILL_H))


func bench_open() -> bool:
	return _bench != null and _bench.is_open


func open_bench() -> void:
	if _bench != null:
		_bench.open()


## Shuts the bench's drawer; true when it was open, so the screen's Back handler
## can stop there.
func close_bench() -> bool:
	return _bench != null and _bench.close()


## Day, twilight or night for this match (OvalStadium.time_of_day; a capture or a
## test may set `time_override`).
var time_override := ""

func time_of_day(weather := "") -> String:
	return time_override if time_override != "" else OvalStadium.time_of_day(weather)


## Which way the breeze blows along the ground as it is drawn now, +1 or -1 on the
## flat frame's long axis: toward the end the side kicking with it in the first
## quarter kicks to then. That end is a fixed part of the ground; the sides change
## ends, the flags do not. The match's own breeze is read, never changed; a result
## that does not carry it and has no live match behind it blows to the +1 end.
func breeze_toward() -> float:
	var sim = null
	if not result.has("breeze_side"):
		var gs := get_node_or_null("/root/GameState")
		if gs != null and "pending_sim" in gs:
			sim = gs.get("pending_sim")
			# Only the match on this oval: another match's breeze is not this one's.
			if sim != null and (sim.squads.size() < 2 or str(sim.squads[0].code) != home_code 					or str(sim.squads[1].code) != away_code):
				sim = null
	return OvalStadium.breeze_toward(result, sim)


func _club_colours() -> Array:
	var cols := []
	for code in [home_code, away_code]:
		if str(code) != "":
			cols.append(GameDB.club_colours(str(code)))
	return cols


## One disc: the kit, a dark edge, and the number in white with a full dark edge
## (eight directions) so it reads on a white stripe as well as on navy.
func _draw_disc(p: Vector2, r: float, kit: Dictionary, label: String, fs: int) -> void:
	paint_disc(self, p, r, kit, label, fs, antialias)


static func paint_disc(ci: CanvasItem, p: Vector2, r: float, kit: Dictionary, label: String, fs: int, aa: bool) -> void:
	ci.draw_circle(p + Vector2(0, r * 0.22), r, Color(0, 0, 0, 0.28))
	paint_kit(ci, p, r, kit, aa)
	ci.draw_circle(p, r, Color(0, 0, 0, 0.45), false, 1.2, aa)
	if label == "":
		return
	var font := UiKit.BOLD
	var inks := number_inks(kit)
	var w := font.get_string_size(label, HORIZONTAL_ALIGNMENT_CENTER, -1, fs).x
	var origin := p + Vector2(-w * 0.5, fs * 0.36)
	for off in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1),
			Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		ci.draw_string(font, origin + off, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, inks[1])
	ci.draw_string(font, origin, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, inks[0])


## Where the ball is drawn on the turf, in pixels: in a player's hands it goes
## where his disc is drawn.
func ball_point() -> Vector2:
	var ground := _w2s(director.ball.get("pos", Vector2.ZERO))
	var holder := int(director.ball.get("holder", -1))
	if str(director.ball.get("mode", "")) == "held" and holder >= 0 and holder < _nudge.size():
		ground += _nudge[holder]
	return ground


## A side's tokens: a disc in the club's home kit (its base colour and its
## design in the pattern colour), the number on it in white with a dark edge
## so it reads on any kit. Each disc at its own size (disc_radius).
func _draw_tokens(full: float) -> void:
	var font := UiKit.BOLD
	for id in draw_order():
		var t: Dictionary = director.tokens[id]
		var kit: Dictionary = _kits[int(t["side"])]
		var base: Color = kit.get("base", Color.WHITE)
		var p := _disc_at(int(t["id"]))
		if p.x < -full * 3.0 or p.y < -full * 3.0 or p.x > size.x + full * 3.0 or p.y > size.y + full * 3.0:
			continue
		# The size this disc is drawn at now, and the number with it.
		var tr := disc_radius(int(t["id"]))
		var fs := number_size(tr)
		if float(t["down"]) > 0.0:
			# On the ground after a tackle.
			draw_colored_polygon(_ellipse_points(p, tr * 1.15, tr * 0.62, 16), base.darkened(0.25))
			draw_polyline(_ellipse_points(p, tr * 1.15, tr * 0.62, 16), Color(0, 0, 0, 0.4), 1.2, antialias)
			continue
		# Drop shadow keeps tokens readable on the stripes.
		draw_circle(p + Vector2(0, tr * 0.22), tr, Color(0, 0, 0, 0.28))
		_draw_kit(p, tr, kit)
		_shade_disc(p, tr, base)
		var label := str(t["num"])
		var w := font.get_string_size(label, HORIZONTAL_ALIGNMENT_CENTER, -1, fs).x
		var origin := p + Vector2(-w * 0.5, fs * 0.36)
		# A full dark edge (eight directions) so the white figure reads on a
		# white stripe as well as on navy.
		var inks := number_inks(kit)
		for off in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1),
				Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
			draw_string(font, origin + off, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, inks[1])
		draw_string(font, origin, label, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, inks[0])
	# Tired and hurt marks over every disc, so none hides under a neighbour.
	for t2 in director.tokens:
		var m: Dictionary = marks.get(str(t2.get("pid", "")), {})
		if m.is_empty() or float(t2["down"]) > 0.0:
			continue
		var p2 := _disc_at(int(t2["id"]))
		if p2.x < -full * 3.0 or p2.y < -full * 3.0 or p2.x > size.x + full * 3.0 or p2.y > size.y + full * 3.0:
			continue
		PlayerMarks.paint(self, p2, disc_radius(int(t2["id"])), str(m["mark"]), antialias)


## The long press's words: the player's name and what his mark means, in a
## dark box over his disc, kept inside the view.
func _draw_tip() -> void:
	if tip.is_empty():
		return
	draw_set_transform(Vector2.ZERO)
	var fs := 14
	var who := str(tip.get("name", ""))
	var text := str(tip["text"])
	var nw := UiKit.BOLD.get_string_size(who, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var tw := UiKit.FONT.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
	var pad := 8.0
	var w := maxf(nw, tw) + pad * 2.0
	var lines := 2 if who != "" else 1
	var h := float(fs) * 1.35 * lines + pad * 2.0 - 4.0
	var at: Vector2 = tip["at"]
	var r := float(tip["r"])
	var box := Rect2(at.x - w * 0.5, at.y - r * 1.6 - h, w, h)
	if box.position.y < 4.0:
		box.position.y = at.y + r * 1.6
	box.position.x = clampf(box.position.x, 4.0, maxf(4.0, size.x - w - 4.0))
	box.position.y = clampf(box.position.y, 4.0, maxf(4.0, size.y - h - 4.0))
	draw_rect(box, Color(0.05, 0.05, 0.06, 0.94))
	draw_rect(box, Color(RING_COLOUR, 0.5), false, 1.0)
	var y := box.position.y + pad + fs * 0.95
	if who != "":
		draw_string(UiKit.BOLD, Vector2(box.position.x + pad, y), who, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, RING_COLOUR)
		y += fs * 1.35
	draw_string(UiKit.FONT, Vector2(box.position.x + pad, y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, RING_COLOUR)


## PROTOTYPE: the six nearest the ball as figures, each a slot for the
## MiniFigures layer: feet on the token, the jog strip when he moves (side-on
## across the screen, back or front along it), idle when he stands, the
## number on his back when he shows it and the figure is tall enough.
func _figure_slots(tr: float) -> Array:
	var out := []
	if director.ball.is_empty():
		return out
	var ball_pos: Vector2 = director.ball["pos"]
	var order := []
	for i in range(director.tokens.size()):
		var t: Dictionary = director.tokens[i]
		if float(t.get("down", 0.0)) > 0.0:
			continue
		order.append([(t["pos"] as Vector2).distance_squared_to(ball_pos), i])
	order.sort_custom(func(a, b): return a[0] < b[0])
	var height_px := float(VignetteFigures.BODIES["average"]["height_m"]) * VignetteFigures.PX_PER_M
	var k := FIGURE_HEIGHT * tr / height_px
	var m := end_sign(period)
	for j in range(mini(FIGURES_NEAR_BALL, order.size())):
		var i: int = order[j][1]
		var t: Dictionary = director.tokens[i]
		var p := _disc_at(i)
		if p.x < -tr * 4.0 or p.y < -tr * 4.0 or p.x > size.x + tr * 4.0 or p.y > size.y + tr * 4.0:
			continue
		var vel: Vector2 = t.get("vel", Vector2.ZERO)
		var moving := vel.length() > 0.6
		var anim := "jog" if moving else "idle"
		var facing := "front"
		var mirror := false
		if moving:
			# Which way he runs on the screen (turned with the ground).
			var sv := Vector2(vel.x * m, vel.y)
			if upright:
				sv = Vector2(sv.y, -sv.x)
			if absf(sv.x) > absf(sv.y):
				facing = "side_l"
				mirror = sv.x > 0.0
			else:
				facing = "back" if sv.y < 0.0 else "front"
		# A move the sheet lacks is stood in for (the picture-truth suite reads this).
		var fallback := not VignetteFigures.has("average", anim, facing)
		if fallback:
			anim = "idle"
			facing = "front"
		var info := VignetteFigures.strip("average", anim, facing)
		var frames := int(info["frames"])
		var frame := (int(Time.get_ticks_msec() / 90) + i * 3) % frames if moving else 0
		var look := _look_for(str(t.get("pid", "")))
		var kit := int(t["side"])
		var number := Color(0, 0, 0, 0)
		if facing.begins_with("back") and FIGURE_HEIGHT * tr > 18.0:
			number = StoppageVignette.number_colour(kit, int(t["num"]), 1.0, mirror)
		out.append({"feet": p + Vector2(0, tr * 0.3), "info": info, "frame": frame, "k": k,
				"colour": StoppageVignette.look_colour(kit, look, mirror), "mirror": mirror,
				"number": number, "hair": str(look.get("hair_style", VignetteFigures.HAIR_BASE)),
				"face": StoppageVignette.face_of(look), "ink": StoppageVignette.ink_of(look),
				"anim": anim, "facing": facing, "fallback": fallback})
	# The man lower on the screen stands in front.
	out.sort_custom(func(a, b): return (a["feet"] as Vector2).y < (b["feet"] as Vector2).y)
	return out


## His skin, hair and sleeves (GameDB.figure_look), found once per player.
func _look_for(pid: String) -> Dictionary:
	if not _looks.has(pid):
		var p = GameDB.player_by_id(pid)
		_looks[pid] = GameDB.figure_look(p, str(result.get("weather", "")) == "wet") if p != null \
				else StoppageVignette.UMPIRE_LOOK
	return _looks[pid]


## The club's design on a disc: stripes, hoops, a sash, a yoke, a band, a
## chevron or side panels in the pattern colour over the base; anything else
## is the base with an inner disc of the pattern colour. Shapes are drawn
## within the disc's chord so nothing pokes out of the circle.
## The light on the turf, one radial texture for every match: a soft pool of
## light over the middle, the grass falling darker into the fence's shadow.
static var _light_tex: Texture2D = null

static func _light_texture() -> Texture2D:
	if _light_tex == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.55, 0.85, 1.0])
		g.colors = PackedColorArray([Color(1.0, 1.0, 0.9, 0.10), Color(1.0, 1.0, 0.95, 0.0),
				Color(0.0, 0.02, 0.0, 0.12), Color(0.0, 0.02, 0.0, 0.30)])
		var t := GradientTexture2D.new()
		t.gradient = g
		t.fill = GradientTexture2D.FILL_RADIAL
		t.fill_from = Vector2(0.5, 0.5)
		t.fill_to = Vector2(1.0, 0.5)
		t.width = 128
		t.height = 128
		_light_tex = t
	return _light_tex


## A disc with some body: lit from above (a light edge on its top, a darker one
## underneath), and a light outline on a dark kit so navy or black still stands
## off the dark green (Carlton, Collingwood, Fremantle at 18 px).
func _shade_disc(p: Vector2, tr: float, base: Color) -> void:
	draw_arc(p, tr - 0.8, PI * 1.08, PI * 1.92, 16, Color(1, 1, 1, 0.32), 1.4, antialias)
	draw_arc(p, tr - 0.8, PI * 0.12, PI * 0.88, 16, Color(0, 0, 0, 0.30), 1.4, antialias)
	var edge := Color(1, 1, 1, 0.7) if base.get_luminance() < 0.22 else Color(0, 0, 0, 0.45)
	draw_circle(p, tr, edge, false, 1.3, antialias)


func _draw_kit(p: Vector2, tr: float, kit: Dictionary) -> void:
	paint_kit(self, p, tr, kit, antialias)


## The kit on any canvas item (the oval's discs, the audit board).
static func paint_kit(ci: CanvasItem, p: Vector2, tr: float, kit: Dictionary, aa: bool) -> void:
	var base: Color = kit.get("base", Color.WHITE)
	var pat: Color = kit.get("pattern", Color.DIM_GRAY)
	var design := disc_design(kit)
	ci.draw_circle(p, tr, base)
	var r := tr * 0.94
	match design:
		"stripes":
			for x in [-0.55, 0.0, 0.55]:
				var cx := float(x) * r
				var half := sqrt(maxf(0.0, r * r - cx * cx)) * 0.98
				ci.draw_rect(Rect2(p + Vector2(cx - r * 0.13, -half), Vector2(r * 0.26, half * 2.0)), pat)
		"hoops", "lowhoops", "twohoops", "tiers":
			for y in [-0.4, 0.3]:
				var cy := float(y) * r
				var half := sqrt(maxf(0.0, r * r - cy * cy)) * 0.98
				ci.draw_rect(Rect2(p + Vector2(-half, cy - r * 0.15), Vector2(half * 2.0, r * 0.3)), pat)
		"sash":
			var w := r * 0.42
			ci.draw_colored_polygon(PackedVector2Array([p + Vector2(-r * 0.75, -r * 0.75 + w), p + Vector2(-r * 0.75, -r * 0.75),
					p + Vector2(r * 0.75, r * 0.75 - w), p + Vector2(r * 0.75, r * 0.75)]), pat)
		"yoke", "shoulders":
			# The top near-half, so the two colours read at 18 px: the arc from
			# chord end to chord end (the chord closes it), never a bow-tie.
			var pts := PackedVector2Array()
			var lift := asin(0.05)
			for i in range(15):
				var ang := lerpf(PI + lift, TAU - lift, float(i) / 14.0)
				pts.append(p + Vector2(cos(ang) * r, sin(ang) * r))
			ci.draw_colored_polygon(pts, pat)
		"band":
			ci.draw_rect(Rect2(p + Vector2(-r * 0.98, -r * 0.22), Vector2(r * 1.96, r * 0.44)), pat)
		"chevron", "chevrons", "wings":
			ci.draw_polyline(PackedVector2Array([p + Vector2(-r * 0.7, -r * 0.35), p + Vector2(0, r * 0.4),
					p + Vector2(r * 0.7, -r * 0.35)]), pat, maxf(2.0, r * 0.32), aa)
		"panels", "sides", "giants", "map":
			var pts := PackedVector2Array()
			for i in range(17):
				var ang := PI * 0.5 + PI * float(i) / 16.0
				pts.append(p + Vector2(cos(ang) * r, sin(ang) * r))
			ci.draw_colored_polygon(pts, pat)
		_:
			ci.draw_circle(p, tr * 0.55, pat)
	var ring = kit.get("ring", null)
	if ring != null:
		# The club's third colour round the rim, clear of the number.
		ci.draw_arc(p, tr * 0.88, 0.0, TAU, 28, ring, maxf(2.0, tr * 0.2), aa)


func _readable_on(bg: Color) -> Color:
	var lum := 0.299 * bg.r + 0.587 * bg.g + 0.114 * bg.b
	return Color(0.08, 0.08, 0.1) if lum > 0.55 else Color(1, 1, 1)


## The real 50m arc dies where it meets the boundary, so walk in from each end
## of the inward-facing half circle and keep only the span inside the oval.
func _arc_span(c: Vector2, a: float, b: float, goal: Vector2, r: float) -> Vector2:
	var base := atan2(c.y - goal.y, c.x - goal.x)
	var lo := base - PI * 0.5
	var hi := base + PI * 0.5
	var a0 := lo
	var a1 := hi
	var steps := 64
	for i in range(steps + 1):
		var ang := lerpf(lo, hi, float(i) / float(steps))
		if _inside_oval(c, a, b, goal + Vector2(cos(ang), sin(ang)) * r):
			a0 = ang
			break
	for i in range(steps + 1):
		var ang := lerpf(hi, lo, float(i) / float(steps))
		if _inside_oval(c, a, b, goal + Vector2(cos(ang), sin(ang)) * r):
			a1 = ang
			break
	return Vector2(a0, a1)


func _inside_oval(c: Vector2, a: float, b: float, p: Vector2) -> bool:
	var dx := (p.x - c.x) / a
	var dy := (p.y - c.y) / b
	return dx * dx + dy * dy <= 1.0


## Positions in metres and on screen, for the capture tool and tests.
func debug_snapshot() -> Dictionary:
	var snap := director.snapshot()
	var screen := []
	for t in director.tokens:
		screen.append(_w2s(t["pos"]))
	snap["screen"] = screen
	snap["drawn"] = _disc
	snap["bench"] = director.bench
	snap["ball_screen"] = _w2s(director.ball.get("pos", Vector2.ZERO))
	return snap


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_cam = _clamp_cam(_cam)
		queue_redraw()
