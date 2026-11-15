extends SceneTree
## One tackle of a seeded match on the 3D oval, filmed close (row 197):
##   godot --windowed --path . --script tools/visual/capture_oval3d_tackle.gd -- OUTDIR [K] [SEED]
## Fremantle v St Kilda (seed 31) at 60 frames a second, as measure_oval3d_tackles.gd plays it,
## so tackle K here is tackle K there. A first pass plays without drawing and logs where every
## man is over the window (from LEAD_IN before the take starts to TAIL after the arms meet). The
## camera is then placed from those positions: side-on to the run-in, at eye height, and turned
## up to 60 degrees round the tackle until no other man stands between it and either of the two (tested on every
## logged frame; higher when side-on is blocked). A second pass plays again and saves every other frame of the window, with a
## wing (game camera) still at the contact. Prints the camera and how many frames were blocked.

const DT := 1.0 / 60.0
const LEAD_IN := 0.3           # s filmed before the take starts
const TAIL := 0.9              # s filmed after the arms meet
const SIZE := Vector2i(1280, 720)
const BODY_R := 0.35           # m: a man's body, for the line of sight
const BODY_H := 1.9            # m: and how tall it stands


func _initialize() -> void:
	_run.call_deferred()
	create_timer(600.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_tackle"
	var want := int(args[1]) if args.size() > 1 else 0
	var seed := int(args[2]) if args.size() > 2 else 31
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	DisplayServer.window_set_size(SIZE)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	res["label"] = "Round 1"

	# Pass 1: find the tackle and log every man's hips over its window.
	var a := _match(res)
	var d = a[0]
	var oval = a[1]
	var n := 0
	var log := []               # per frame: [hips per player]
	var start_n := -1
	var hit_n := -1
	var rec := {}
	while n < 60 * 60 * 40:
		d.advance(DT)
		oval.sync(DT)
		n += 1
		var tk: Array = oval.anim.tackles
		if start_n < 0 and tk.size() > want:
			rec = tk[want]
			start_n = n
		if start_n >= 0:
			var hips := []
			for p in oval.players:
				var h: Transform3D = oval.anim._hips_world(p)
				hips.append(h.origin)
			log.append(hips)
			if hit_n < 0 and float(rec["hit_t"]) >= 0.0:
				hit_n = n
			if hit_n >= 0 and n >= hit_n + int(TAIL / DT):
				break
	if start_n < 0 or hit_n < 0:
		print("NO TACKLE %d" % want)
		quit(1)
		return
	oval.queue_free()
	await process_frame
	var who := int(rec["who"])
	var v := int(rec["victim"])
	# Logged frames start at start_n; the window adds LEAD_IN before it (assume the men there
	# are where they are at start_n for the sight test).
	var K: Vector3 = log[0][who]
	var V: Vector3 = log[0][v]
	var C: Vector3 = log[hit_n - start_n][v]
	var mid := (K + V + 2.0 * C) / 4.0
	var run := Vector2(V.x - K.x, V.z - K.z).normalized()
	var side := Vector2(-run.y, run.x)
	# Side-on first (so neither man hides the other), then up to 60 degrees round either way,
	# from either side, then higher: the first view with nobody in the way wins.
	var best := []
	for height in [1.7, 3.5, 5.5]:
		for ang in [0.0, 30.0, -30.0, 60.0, -60.0, 180.0, 150.0, -150.0, 120.0, -120.0]:
			var dir := side.rotated(deg_to_rad(ang))
			for dist in [9.0, 7.0]:
				var eye := Vector3(mid.x + dir.x * dist, height, mid.z + dir.y * dist)
				var blocked := 0
				for f in range(log.size()):
					if _blocked(eye, log[f], who, v):
						blocked += 1
				if best.is_empty() or blocked < int(best[1]):
					best = [eye, blocked, ang, dist]
				if blocked == 0:
					break
			if int(best[1]) == 0:
				break
		if int(best[1]) == 0:
			break
	var eye: Vector3 = best[0]
	var look := Vector3(mid.x, 0.9, mid.z)
	print("TACKLE %d %s who %d victim %d start frame %d hit frame %d | from %s stand %s contact hips %s" % [
			want, rec["pair"], who, v, start_n, hit_n, K, V, C])
	print("CAMERA eye %s look %s | %+.0f deg off side-on, %.0f m | blocked %d of %d frames" % [
			eye, look, float(best[2]), float(best[3]), int(best[1]), log.size()])

	# Pass 2: play again, film the window.
	a = _match(res)
	d = a[0]
	oval = a[1]
	var first := start_n - int(LEAD_IN / DT)
	var last := hit_n + int(TAIL / DT)
	n = 0
	var hit2 := -1
	while n < last:
		d.advance(DT)
		oval.sync(DT)
		n += 1
		var tk2: Array = oval.anim.tackles
		if hit2 < 0 and tk2.size() > want and float(tk2[want]["hit_t"]) >= 0.0:
			hit2 = n
			var r: Dictionary = tk2[want]
			var at: Vector2 = r["at"]
			print("FILMED TACKLE %s lead %.2f late %+.3f s | hips %.2f arms %.2f m from spot | warp %.2f m | turn %+.0f deg" % [
					r["pair"], float(r["lead"]), float(r["hit_t"]) - float(r["event_t"]),
					(r["root"] as Vector2).distance_to(at) if at != Vector2.INF else NAN,
					(r["contact"] as Vector2).distance_to(at) if at != Vector2.INF else NAN,
					float(r["warp_m"]), float(r["turn_deg"])])
		if n < first:
			continue
		if n == hit_n:
			oval.aim_wing(30.0, 70.0)
			await _save(out, "wing_contact")
		oval.camera.global_position = eye
		oval.camera.fov = 40.0
		oval.camera.look_at(look, Vector3.UP)
		if (n - first) % 2 == 0:
			await _save(out, "f%03d" % ((n - first) / 2))
		else:
			await process_frame
	print("FILMED frames %d-%d (arms meet at %d, first pass %d) every 2nd to %s" % [first, last, hit2, hit_n, out])
	quit()


func _match(res: Dictionary) -> Array:
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	return [d, oval]


## True when another man's body stands on the sight line from the eye to either man's hips.
func _blocked(eye: Vector3, hips: Array, who: int, v: int) -> bool:
	for target in [who, v]:
		var to: Vector3 = hips[target]
		var e := Vector2(eye.x, eye.z)
		var t := Vector2(to.x, to.z)
		for j in range(hips.size()):
			if j == who or j == v:
				continue
			var o := Vector2((hips[j] as Vector3).x, (hips[j] as Vector3).z)
			var seg := t - e
			var u := clampf((o - e).dot(seg) / maxf(seg.length_squared(), 1e-6), 0.0, 1.0)
			# The sight line passes his body below his head (a man is about 1.9 m tall).
			var y := lerpf(eye.y, to.y, u)
			if u > 0.02 and u < 0.98 and y < BODY_H and (e + seg * u).distance_to(o) < BODY_R:
				return true
	return false


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
