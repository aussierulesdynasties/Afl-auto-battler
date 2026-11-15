extends SceneTree
## Bodies going round each other on the 3D oval (MatchMotion.avoid, hold_apart), filmed:
##   godot --windowed --path . --script tools/visual/capture_oval3d_crowd.gd -- OUTDIR [SEED]
## Fremantle v St Kilda (seed 31) at 60 frames a second. A first pass plays the director alone
## and logs every man over the first MINUTES of presentation, then picks two windows:
##   A, the busiest set-up: the moment most pairs not meant to touch run within 2 m of each
##      other while closing (where avoiding has work to do), and the men round them;
##   B, the biggest ball-up pack: from the pack forming to the ball coming out.
## Each camera follows its group from the logged positions: it looks at the group's centre
## (smoothed over half a second) from a fixed elevated three-quarter offset, turned round the
## group until every man in it projects inside the frame on every logged frame, with the fewest
## frames where one of them hides another. A second pass plays the director and the oval
## again and saves every other frame of each window (30 a second: real speed).

const DT := 1.0 / 60.0
const MINUTES := 14.0          # presentation minutes searched
const SIZE := Vector2i(1280, 720)
const FOV := 40.0
const WARM := 6
const BODY_R := 0.3            # m: a man's body, for the line of sight
const BODY_H := 1.9
const SMOOTH := 15             # frames each side the camera's aim is averaged over


func _initialize() -> void:
	_run.call_deferred()
	create_timer(900.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_crowd"
	var seed := int(args[1]) if args.size() > 1 else 31
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	DisplayServer.window_set_size(SIZE)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	res["label"] = "Round 1"

	# Pass 1: the director alone (contacts on, as the oval sets them), every man logged.
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	d.want_contacts = true
	var log := []
	var best_setup := [-1, 0, []]               # frame, pairs, the men in them
	var best_pack := [-1, 0, []]                # frame, men within 3 m of the ball-up, them
	var n := 0
	while n < int(MINUTES * 60.0 * 60.0) and not d.idle():
		d.advance(DT)
		d.contacts.clear()
		var row := PackedVector2Array()
		for t in d.tokens:
			row.append(t["pos"])
		log.append(row)
		var p: Dictionary = d._phases[d._pi] if d._pi < d._phases.size() else {}
		var kind := str(p.get("t", ""))
		var k := int(d._beat.get("k", -1))
		if kind == "setup":
			# Where the most such pairs crowd together (a set-up spans the ground).
			var meant: Dictionary = d._meant_now()
			var mids := []
			var men := []
			for i in range(row.size()):
				for j in range(i + 1, row.size()):
					var w: Vector2 = row[j] - row[i]
					if w.length() > 2.0 or (meant.has(i) and meant.has(j)):
						continue
					var cl: float = -((d.tokens[j]["vel"] as Vector2) - (d.tokens[i]["vel"] as Vector2)).dot(w.normalized())
					if cl > 2.0:
						mids.append((row[i] + row[j]) * 0.5)
						men.append([i, j])
			for a in range(mids.size()):
				var cnt := 0
				var ids := {}
				for b in range(mids.size()):
					if (mids[b] as Vector2).distance_to(mids[a]) <= 6.0:
						cnt += 1
						ids[men[b][0]] = true
						ids[men[b][1]] = true
				if cnt > int(best_setup[1]):
					best_setup = [n, cnt, ids.keys()]
		elif str(d._beat.get("kind", "")) == "ballup" and kind in ["pack", "throwup"]:
			var at: Vector2 = p.get("at", Vector2.ZERO)
			var near := []
			for i in range(row.size()):
				if row[i].distance_to(at) <= 3.0:
					near.append(i)
			if near.size() > int(best_pack[1]):
				best_pack = [n, near.size(), near]
		n += 1
	var frames := log.size()
	print("PASS1 %d frames" % frames)
	var shots := []
	if int(best_setup[0]) >= 0:
		var f0: int = maxi(0, int(best_setup[0]) - 120)
		var f1: int = mini(frames - 1, int(best_setup[0]) + 120)
		shots.append(_shot("A_setup", log, f0, f1, best_setup[2], int(best_setup[0]) - 15, int(best_setup[0]) + 15))
		print("SETUP peak frame %d with %d closing pairs within 6 m, men %s" % [best_setup[0], best_setup[1], best_setup[2]])
	if int(best_pack[0]) >= 0:
		var pf := int(best_pack[0])
		shots.append(_shot("B_pack", log, maxi(0, pf - 90), mini(frames - 1, pf + 150), best_pack[2], pf - 5, pf + 5))
		print("PACK frame %d, %d men within 3 m of the ball-up: %s" % [pf, best_pack[1], best_pack[2]])
	for s in shots:
		print("SHOT %s frames %d-%d | %d men | offset %s (%.1f m back) | all in frame %s | hidden %d of core %s" % [
				s["name"], s["f0"], s["f1"], (s["ids"] as Array).size(), s["off"], (s["off"] as Vector3).length(), s["in"], s["hid"], s["core"]])

	# Pass 2: the director and the oval, each window filmed.
	d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var last := 0
	for s in shots:
		last = maxi(last, int(s["f1"]))
	n = 0
	var drift := 0.0
	while n <= last:
		d.advance(DT)
		oval.sync(DT)
		var shot: Dictionary = {}
		for s in shots:
			if n >= int(s["f0"]) - WARM and n <= int(s["f1"]):
				shot = s
		if shot.is_empty():
			n += 1
			continue
		for i in range(d.tokens.size()):
			drift = maxf(drift, (d.tokens[i]["pos"] as Vector2).distance_to((log[n] as PackedVector2Array)[i]))
		var aim: Vector3 = (shot["aims"] as Array)[clampi(n - int(shot["f0"]), 0, (shot["aims"] as Array).size() - 1)]
		oval.camera.global_position = aim + (shot["off"] as Vector3)
		oval.camera.fov = FOV
		oval.camera.look_at(aim, Vector3.UP)
		var f := n - int(shot["f0"])
		if f >= 0 and f % 2 == 0:
			await _save(out, "%s_%03d" % [shot["name"], f / 2])
		else:
			await process_frame
		n += 1
	print("FILMED to %s | pass 2 drifted %.3f m from the logged positions at most" % [out, drift])
	quit()


## A camera following men `ids` over frames f0..f1 of `log`: each frame's aim is their centre
## smoothed over SMOOTH frames each side, framed so all of them stay in shot over the core
## frames c0..c1 (the moment itself; before and after it they may run out of shot).
func _shot(name: String, log: Array, f0: int, f1: int, ids: Array, c0: int, c1: int) -> Dictionary:
	c0 = clampi(c0, f0, f1)
	c1 = clampi(c1, f0, f1)
	var mids := []
	for f in range(f0, f1 + 1):
		var m := Vector2.ZERO
		for i in ids:
			m += (log[f] as PackedVector2Array)[i]
		mids.append(m / float(maxi(ids.size(), 1)))
	var aims := []
	var rad := 2.0
	for f in range(f0, f1 + 1):
		var a := Vector2.ZERO
		var c := 0
		for g in range(maxi(f0, f - SMOOTH), mini(f1, f + SMOOTH) + 1):
			a += mids[g - f0]
			c += 1
		a /= float(c)
		aims.append(Vector3(a.x, 0.9, a.y))
		if f >= c0 and f <= c1:
			for i in ids:
				rad = maxf(rad, ((log[f] as PackedVector2Array)[i]).distance_to(a))
	var best := {}
	for height_k in [0.55, 0.8]:
		for a in range(12):
			var dir := Vector2.from_angle(TAU * float(a) / 12.0)
			var back := (rad + 1.0) / tan(deg_to_rad(FOV) * 0.5)
			var off := Vector3(dir.x * back, back * height_k, dir.y * back)
			var inside := true
			var hid := 0
			for f in range(c0, c1 + 1, 2):
				var rw: PackedVector2Array = log[f]
				var aim: Vector3 = aims[f - f0]
				for i in ids:
					for y in [0.0, BODY_H]:
						var q := _project(aim + off, aim, Vector3(rw[i].x, y, rw[i].y))
						if absf(q.x) > 0.92 or absf(q.y) > 0.92:
							inside = false
				if _any_hidden(aim + off, rw, ids):
					hid += 1
			var score := (0 if inside else 100000) + hid
			if best.is_empty() or score < int(best["score"]):
				best = {"name": name, "f0": f0, "f1": f1, "ids": ids, "off": off, "aims": aims, "in": inside,
						"hid": hid, "score": score, "core": [c0, c1]}
	return best


## Where `p` lands on screen from `eye` looking at `look`: -1..1 across and up.
func _project(eye: Vector3, look: Vector3, p: Vector3) -> Vector2:
	var fwd := (look - eye).normalized()
	var right := fwd.cross(Vector3.UP).normalized()
	var up := right.cross(fwd)
	var v := p - eye
	var z := v.dot(fwd)
	if z <= 0.1:
		return Vector2(9, 9)
	var ty := tan(deg_to_rad(FOV) * 0.5)
	var tx := ty * float(SIZE.x) / float(SIZE.y)
	return Vector2(v.dot(right) / (z * tx), v.dot(up) / (z * ty))


## True when one of `ids` stands on the sight line from the eye to another one's chest.
func _any_hidden(eye: Vector3, row: PackedVector2Array, ids: Array) -> bool:
	var e := Vector2(eye.x, eye.z)
	for a in ids:
		var t := row[a]
		var seg := t - e
		for b in ids:
			if b == a:
				continue
			var o := row[b]
			var u := clampf((o - e).dot(seg) / maxf(seg.length_squared(), 1e-6), 0.0, 1.0)
			var y := lerpf(eye.y, 1.3, u)
			if u > 0.02 and u < 0.98 and y < BODY_H and (e + seg * u).distance_to(o) < BODY_R:
				return true
	return false


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(out.path_join(name + ".png"))
