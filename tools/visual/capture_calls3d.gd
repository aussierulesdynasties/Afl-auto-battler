extends SceneTree
## Row 201 proof films (docs/3D_VIEW_PLAN.md step 1.5): each coach's call beside Balanced on the
## same seeded match, on the 3D oval, from a high whole-ground camera and the game's broadcast camera.
##   godot --path . --script tools/visual/capture_calls3d.gd -- OUTDIR [call ...]
## Writes OUTDIR/<call>/<arm>_<cam>/fNNN.png at 24 frames a second of the game's 1x (pauses at 2x,
## as PitchView plays them, rule 2.93); tools/visual/calls3d_films.py stacks them into one mp4 a call.
## Fremantle (home, side 0) makes the call; St Kilda stays Balanced.
## The window for each call is the first stretch of Q1 where the call shows (its phase), found by
## playing the Balanced match once and logging possession and stoppages.

const W := 1920
const H := 1080
const DT := 1.0 / 24.0
const SECONDS := 12.0
const SEED := 31
## [file name, label, plan, bursts, phase it shows in]
const CALLS := [
	["press", "Defensive press", "defensive", [], "without"],
	["flood", "Flood behind the ball", "balanced", ["flood"], "without"],
	["stack", "Stack the stoppage", "balanced", ["stack"], "centre"],
	["corridor", "Attack corridor", "attacking", [], "with"],
	["controlled", "Controlled tempo", "controlled", [], "with"],
	["contest", "Win contest", "contest", [], "stoppage"],
	["surge", "Throw numbers at it", "balanced", ["surge"], "with"],
	["hold", "Slow it down", "balanced", ["hold"], "with"],
	["push", "Push numbers forward", "balanced", ["push"], "with"],
]
## The game's PC broadcast camera (PitchView._sync_3d, wide screen).
const WING_UP := 18.0
const WING_BACK := 28.0 * 1.3

var _label: Label
var MD   # MatchDirector, loaded (a --script run cannot name autoload-dependent classes)
var OV   # Oval3D


func _initialize() -> void:
	_run.call_deferred()
	create_timer(5400.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	MD = load("res://scripts/ui/match/MatchDirector.gd")
	OV = load("res://scripts/ui/match/Oval3D.gd")
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://calls3d"
	var only := args.slice(1)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = Vector2i(W, H)
	DisplayServer.window_set_size(Vector2i(W, H))
	var layer := CanvasLayer.new()
	root.add_child(layer)
	_label = Label.new()
	_label.position = Vector2(24, 18)
	_label.add_theme_font_size_override("font_size", 34)
	_label.add_theme_color_override("font_color", Color.WHITE)
	_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_label.add_theme_constant_override("outline_size", 10)
	layer.add_child(_label)

	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), SEED).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	res["label"] = "Round 1"
	var phases := _scout(_with_call(res, "balanced", []))
	for c in CALLS:
		if not only.is_empty() and not only.has(str(c[0])):
			continue
		var start := _window(phases, str(c[4]))
		print("CALL %s: window %.1f s to %.1f s of video" % [str(c[0]), start, start + SECONDS])
		for arm in [["balanced", "Balanced", "balanced", []], ["call", str(c[1]), str(c[2]), c[3]]]:
			await _film(_with_call(res, str(arm[2]), arm[3]), start,
					out.path_join(str(c[0])).path_join(str(arm[0])), str(arm[1]))
	quit()


## Fremantle's call on every timeline entry, St Kilda Balanced (as tests/test_match_marks.gd).
static func _with_call(res: Dictionary, plan: String, bursts: Array) -> Dictionary:
	var r2 := res.duplicate()
	var tl := []
	for e in res["timeline"]:
		var e2: Dictionary = (e as Dictionary).duplicate(true)
		e2["plan"] = plan if int(e2["side"]) == 0 else "balanced"
		e2["bursts"] = bursts if int(e2["side"]) == 0 else []
		tl.append(e2)
	r2["timeline"] = tl
	return r2


## One step of the game's 1x: a pause plays at PAUSE_PLAY, as PitchView._process does.
func _step(d) -> float:
	var h := DT * (float(MD.PAUSE_PLAY) if d.pausing() else 1.0)
	d.advance(h)
	return h


## Q1 of the Balanced match, a frame at a time: what phase Fremantle is in.
func _scout(res: Dictionary) -> Array:
	var d = MD.new()
	d.setup(res, res["events"])
	var log := []
	var t := 0.0
	while t < 900.0 and not d.idle():
		_step(d)
		t += DT
		if d.mode == "break":
			break
		var ph := "with" if d._poss == 0 else "without"
		if d.mode == "centre" or d._centre_stoppage():
			ph = "centre"
		elif d._stoppage_on():
			ph = "stoppage"
		log.append([t, ph])
	return log


## The first start (after the opening bounce, except for a centre call) where the phase holds for
## most of the window and begins it.
func _window(log: Array, phase: String) -> float:
	var need := int(SECONDS / DT)
	var lead := int(1.0 / DT)
	for i in range(log.size() - need):
		if phase != "centre" and float(log[i][0]) < 20.0:
			continue
		if str(log[i][1]) != phase or (i > 0 and str(log[i - 1][1]) == phase):
			continue
		var held := 0
		for k in range(i, i + need):
			if str(log[k][1]) == phase:
				held += 1
		# A bounce or a ball-up is over in a few seconds: it only has to begin the window.
		if held >= (need * 0.6 if phase in ["with", "without"] else int(3.0 / DT)):
			return maxf(0.0, float(log[maxi(0, i - lead)][0]) - DT)
	return 20.0


func _film(res: Dictionary, start: float, out: String, label: String) -> void:
	var d = MD.new()
	d.setup(res, res["events"])
	var oval = OV.new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var t := 0.0
	while t + DT * 0.5 < start:
		oval.sync(_step(d))
		t += DT
	var high_dir := out + "_high"
	var wing_dir := out + "_broadcast"
	DirAccess.make_dir_recursive_absolute(high_dir)
	DirAccess.make_dir_recursive_absolute(wing_dir)
	var worst_off := 0
	var ball_off := 0
	var n := int(SECONDS / DT)
	for i in range(n):
		oval.sync(_step(d))
		_aim_high(oval)
		worst_off = maxi(worst_off, _off_screen(oval))
		_label.text = "%s   (high, whole ground)" % label
		await _save(high_dir, "f%03d" % i)
		oval.aim_wing(WING_UP, WING_BACK)
		if not _ball_on_screen(oval):
			ball_off += 1
		_label.text = "%s   (broadcast)" % label
		await _save(wing_dir, "f%03d" % i)
	print("FILMED %s: %d frames from %.1f s; high camera: at most %d of 36 players off screen; broadcast: ball off screen in %d frames" % [
			out, n, start, worst_off, ball_off])
	oval.queue_free()
	await process_frame


## High above the wing, the whole ground in view: the distance is set so the boundary (an ellipse
## of HALF_LEN by HALF_WID) projects inside the frame with a margin.
func _aim_high(oval) -> void:
	var cam: Camera3D = oval.camera
	var dir := Vector3(0.0, 0.72, 0.69).normalized()
	var dist := 60.0
	for _k in range(80):
		cam.global_position = dir * dist
		cam.look_at(Vector3.ZERO, Vector3.UP)
		if _boundary_fits(cam):
			break
		dist += 3.0


func _boundary_fits(cam: Camera3D) -> bool:
	var m := 0.01
	for k in range(36):
		var a := TAU * float(k) / 36.0
		var p := Vector3(cos(a) * float(MatchMotion.HALF_LEN), 0.0, sin(a) * float(MatchMotion.HALF_WID))
		var s := cam.unproject_position(p)
		if cam.is_position_behind(p) or s.x < W * m or s.x > W * (1.0 - m) or s.y < H * m or s.y > H * (1.0 - m):
			return false
	return true


func _off_screen(oval) -> int:
	var cam: Camera3D = oval.camera
	var off := 0
	for p in oval.players:
		var node: Node3D = p["node"]
		var s := cam.unproject_position(node.global_position)
		if cam.is_position_behind(node.global_position) or s.x < 0 or s.x > W or s.y < 0 or s.y > H:
			off += 1
	return off


func _ball_on_screen(oval) -> bool:
	var cam: Camera3D = oval.camera
	var b: Vector3 = oval.ball.global_position
	var s := cam.unproject_position(b)
	return not cam.is_position_behind(b) and s.x >= 0 and s.x <= W and s.y >= 0 and s.y <= H


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
