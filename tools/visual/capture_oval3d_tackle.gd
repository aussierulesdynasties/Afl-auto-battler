extends SceneTree
## One tackle of a seeded match on the 3D oval, filmed close (row 197):
##   godot --windowed --path . --script tools/visual/capture_oval3d_tackle.gd -- OUTDIR [K] [SEED]
## Fremantle v St Kilda (seed 31) at 60 frames a second, as measure_oval3d_tackles.gd plays it,
## so tackle K here is tackle K there. A first pass plays without drawing and logs where every
## man is over the window (from LEAD_IN before the take starts to TAIL after the arms meet). The
## camera is then placed from those positions: one eye that pans to keep the ball and every man who
## comes within 2 m of it in shot (each while within 6 m of the ball), never within 3 m of any of
## them; side-on to the run-in, at eye height, turned up to 60 degrees round the tackle until no
## other man stands between it and either of the two (tested on every logged frame; higher when
## side-on is blocked). A second pass plays again and saves every other frame of the window, with a
## wing (game camera) still at the contact. Prints the camera and how many frames were blocked.

const DT := 1.0 / 60.0
const LEAD_IN := 0.3           # s filmed before the take starts
const WARM := 6                # frames drawn from the eye before the first one saved
const TAIL := 4.4              # s filmed after the arms meet (the ball spilling out, gathered, fumbled)
const SIZE := Vector2i(1280, 720)
const BODY_R := 0.35           # m: a man's body, for the line of sight
const BODY_H := 1.9            # m: and how tall it stands
const EDGE := 0.85             # the subjects stay inside this share of the frame from its centre
const FOV := 40.0
const NEAR := 6.0             # m: a cast man this close to the ball is in shot
const SMOOTH := 20            # frames either side the pan is averaged over
const CLEAR := 3.0            # m: no cast man comes closer to the eye than this


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
	var balls := []             # per frame: the ball
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
			balls.append(oval.ball.global_position)
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
	# The cast: the two men and every man who comes within 2 m of the ball at any point (whoever
	# runs onto it). On each logged frame the ball and every cast man within NEAR of it must be in
	# shot, boots to head; the eye stays put and pans to follow them (the look is their centre,
	# smoothed over SMOOTH frames either side). No cast man ever comes within CLEAR of the eye, so
	# nobody runs through the camera.
	var cast := {who: true, v: true}
	for f in range(log.size()):
		var b: Vector3 = balls[f]
		for j in range((log[f] as Array).size()):
			var h: Vector3 = log[f][j]
			if Vector2(h.x, h.z).distance_to(Vector2(b.x, b.z)) < 2.0:
				cast[j] = true
	var subj := []              # per frame: the points that must be in shot
	var centre := []
	for f in range(log.size()):
		var b: Vector3 = balls[f]
		var pts := [b]
		for j in cast:
			var h: Vector3 = log[f][j]
			if Vector2(h.x, h.z).distance_to(Vector2(b.x, b.z)) < NEAR:
				pts.append(Vector3(h.x, 0.0, h.z))
				pts.append(Vector3(h.x, BODY_H, h.z))
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		for q in pts:
			lo = Vector2(minf(lo.x, q.x), minf(lo.y, q.z))
			hi = Vector2(maxf(hi.x, q.x), maxf(hi.y, q.z))
		subj.append(pts)
		centre.append(Vector3((lo.x + hi.x) / 2.0, 0.9, (lo.y + hi.y) / 2.0))
	var looks := []
	for f in range(centre.size()):
		var sum := Vector3.ZERO
		var cnt := 0
		for g in range(maxi(0, f - SMOOTH), mini(centre.size(), f + SMOOTH + 1)):
			sum += centre[g]
			cnt += 1
		looks.append(sum / float(cnt))
	var mid: Vector3 = looks[hit_n - start_n]
	var run := Vector2(V.x - K.x, V.z - K.z).normalized()
	var side := Vector2(-run.y, run.x)
	# Side-on first (so neither man hides the other), then up to 60 degrees round either way,
	# from either side, then higher, then further out: the first view with nobody in the way wins.
	var best := []
	for height in [1.7, 3.5, 5.5]:
		for ang in [0.0, 30.0, -30.0, 60.0, -60.0, 180.0, 150.0, -150.0, 120.0, -120.0]:
			var dir := side.rotated(deg_to_rad(ang))
			for dist in [7.0, 9.0, 11.0, 13.0, 16.0]:
				var eye := Vector3(mid.x + dir.x * dist, height, mid.z + dir.y * dist)
				var ok := true
				for f in range(log.size()):
					if not _in_shot(eye, looks[f], subj[f]):
						ok = false
						break
					for j in cast:
						var h: Vector3 = log[f][j]
						if Vector2(h.x, h.z).distance_to(Vector2(eye.x, eye.z)) < CLEAR:
							ok = false
					if not ok:
						break
				if not ok:
					continue
				var blocked := 0
				for f in range(log.size()):
					if _blocked(eye, log[f], who, v):
						blocked += 1
				if best.is_empty() or blocked < int(best[1]):
					best = [eye, blocked, ang, dist]
				if blocked == 0:
					break
			if not best.is_empty() and int(best[1]) == 0:
				break
		if not best.is_empty() and int(best[1]) == 0:
			break
	if best.is_empty():
		print("NO CAMERA keeps the men and the ball in shot")
		quit(1)
		return
	var eye: Vector3 = best[0]
	var look: Vector3 = mid
	print("TACKLE %d %s who %d victim %d start frame %d hit frame %d | from %s stand %s contact hips %s" % [
			want, rec["pair"], who, v, start_n, hit_n, K, V, C])
	print("IN SHOT men %s, the ball" % [cast.keys()])
	print("CAMERA eye %s look at the contact %s, panning | %+.0f deg off side-on, %.0f m | blocked %d of %d frames" % [
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
		if n < first - WARM:
			continue
		if n == hit_n:
			oval.aim_wing(30.0, 70.0)
			await _save(out, "wing_contact")
		oval.camera.global_position = eye
		oval.camera.fov = FOV
		oval.camera.look_at(looks[clampi(n - start_n, 0, looks.size() - 1)], Vector3.UP)
		if n < first or n == hit_n + 1:
			# Drawn, not saved: the shadow maps of the frame the camera jumps to are stale (a dark
			# block over the turf on the first frame after a cut), so the eye settles first.
			await process_frame
			continue
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


## True when every point projects inside EDGE of the frame from an eye looking at `look`.
func _in_shot(eye: Vector3, look: Vector3, pts: Array) -> bool:
	var fwd := (look - eye).normalized()
	var right := fwd.cross(Vector3.UP).normalized()
	var up := right.cross(fwd)
	var ty := tan(deg_to_rad(FOV / 2.0))
	var tx := ty * float(SIZE.x) / float(SIZE.y)
	for p in pts:
		var r: Vector3 = (p as Vector3) - eye
		var z := r.dot(fwd)
		if z < 1.0 or absf(r.dot(right) / (z * tx)) > EDGE or absf(r.dot(up) / (z * ty)) > EDGE:
			return false
	return true


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
