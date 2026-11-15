extends SceneTree
## Every tackle of a seeded match drawn on the 3D oval, measured (row 197):
##   godot --headless --path . --script tools/visual/measure_oval3d_tackles.gd -- [SECONDS] [SEED]
## Fremantle v St Kilda (seed 31 unless given) played through MatchDirector at 60 frames a
## second. Per tackle: the take chosen, its run-in, when the clip's arms meet against the
## director's contact (late, s), where (the tacklee's hips and the arms against the tackle spot,
## m), the tacklee's turn and the tackler's correction over the run-in, the fastest a planted
## foot slides on the ground while the run-in plays (m/s, against the take's own feet over the
## same clip time), and how close the two bodies come before the contact (m, against the take's
## own). Prints one line a tackle and a summary.

const DT := 1.0 / 60.0
const PLANTED := 0.02          # m: a foot this low is on the ground (the jog swings through under 0.05)
const FEET := ["ball_l", "ball_r"]
const TORSO := ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head"]


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var secs := float(args[0]) if args.size() > 0 else 600.0
	var seed := int(args[1]) if args.size() > 1 else 31
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var anim = oval.anim
	var skel0: Skeleton3D = oval.players[0]["skel"]
	var feet := []
	for f in FEET:
		feet.append(skel0.find_bone(f))
	var torso := []
	for b in TORSO:
		torso.append(skel0.find_bone(b))
	var own := _own(oval.players[0], anim, feet, torso)
	var m := {}                 # tackle index -> measures
	var last := {}              # player -> last foot positions
	var jog := []               # planted-foot speeds of men jogging clear of tackles
	var jog_last := {}
	var t := 0.0
	while t < secs:
		d.advance(DT)
		oval.sync(DT)
		t += DT
		for k in range(anim.tackles.size()):
			var r: Dictionary = anim.tackles[k]
			var age := float(anim._clock) - float(r["start_t"])
			if not m.has(k):
				m[k] = {"slide": 0.0, "slide_k": 0.0, "slide_v": 0.0, "near": 9.0}
			var mk: Dictionary = m[k]
			if age > 0.0 and age <= float(r["lead"]) / 0.6 + 0.05 and float(r["hit_t"]) < 0.0:
				for who in [int(r["who"]), int(r["victim"])]:
					var now := _feet(oval.players[who], feet)
					if last.has(who):
						for j in range(now.size()):
							var a: Vector3 = last[who][j]
							var b: Vector3 = now[j]
							if a.y < PLANTED and b.y < PLANTED:
								var sp := Vector2(b.x - a.x, b.z - a.z).length() / DT
								var key := "slide_k" if who == int(r["who"]) else "slide_v"
								mk[key] = maxf(float(mk[key]), sp)
								mk["slide"] = maxf(float(mk["slide"]), sp)
								if OS.get_environment("DEBUG_K") == str(k):
									print("  k%d %s foot%d age %.3f c %.3f y %.3f/%.3f speed %.2f" % [k, key, j, age, float(anim._in[who].get("c", -1.0)), a.y, b.y, sp])
				mk["near"] = minf(float(mk["near"]), _near(oval.players[int(r["who"])], oval.players[int(r["victim"])], torso))
		# Baseline: every 6th frame, the planted feet of men jogging clear of any tackle.
		if int(t / DT) % 6 == 0:
			for j in range(oval.players.size()):
				var pj: Dictionary = oval.players[j]
				if not (anim._in[j] as Dictionary).is_empty() or (pj["anim"] as AnimationPlayer).current_animation != "jog":
					continue
				var now2 := _feet(pj, feet)
				if jog_last.has(j):
					for f in range(now2.size()):
						var a3: Vector3 = jog_last[j][f]
						var b3: Vector3 = now2[f]
						if a3.y < PLANTED and b3.y < PLANTED:
							jog.append(Vector2(b3.x - a3.x, b3.z - a3.z).length() / DT)
		jog_last = {}
		if int(t / DT) % 6 == 5:
			for j in range(oval.players.size()):
				jog_last[j] = _feet(oval.players[j], feet)
		last = {}
		for k in range(anim.tackles.size()):
			var r2: Dictionary = anim.tackles[k]
			for who in [int(r2["who"]), int(r2["victim"])]:
				last[who] = _feet(oval.players[who], feet)
	var lates := []
	var roots := []
	var arms := []
	var slides := []
	var turns := []
	var warps := []
	for k in range(anim.tackles.size()):
		var r: Dictionary = anim.tackles[k]
		var late := float(r["hit_t"]) - float(r["event_t"]) if float(r["hit_t"]) >= 0.0 and float(r["event_t"]) >= 0.0 else NAN
		var at: Vector2 = r["at"]
		var sr := (r["root"] as Vector2).distance_to(at) if at != Vector2.INF and r["root"] != Vector2.INF else NAN
		var sc := (r["contact"] as Vector2).distance_to(at) if at != Vector2.INF and r["contact"] != Vector2.INF else NAN
		var o: Dictionary = own[r["pair"]]
		print("TACKLE %2d t=%6.2f %s lead %.2f late %+.3f s | hips %.2f arms %.2f m from spot | turn %+5.0f deg, tackler warp %.2f m %+4.0f deg | slide tackler %.2f tacklee %.2f (take %.2f) m/s | bodies %.2f (take %.2f) m | from %s stand %s%s" % [
				k, float(r["start_t"]), r["pair"], float(r["lead"]), late, sr, sc, float(r["turn_deg"]),
				float(r["warp_m"]), float(r["warp_deg"]), float(m[k]["slide_k"]), float(m[k]["slide_v"]), float(o["slide"]),
				float(m[k]["near"]), float(o["near"]), r["from"], r["stand"], " | joined from his token" if r["far"] else ""])
		if not is_nan(late):
			lates.append(late)
		if not is_nan(sr):
			roots.append(sr)
			arms.append(sc)
		slides.append(float(m[k]["slide"]))
		turns.append(absf(float(r["turn_deg"])))
		warps.append(float(r["warp_m"]))
	print("SUMMARY %d tackles in %.0f s | late %s | hips-to-spot %s | arms-to-spot %s | |turn| %s | warp m %s | slide m/s %s | jogging feet m/s %s" % [
			anim.tackles.size(), secs, _stats(lates), _stats(roots), _stats(arms), _stats(turns),
			_stats(warps), _stats(slides), _stats(jog)])
	quit()


## Each take's own planted-foot slide over its run-in (LEAD before the contact, from its root
## motion) and its closest bodies up to the contact, on one figure placed nowhere.
func _own(p: Dictionary, anim, feet: Array, torso: Array) -> Dictionary:
	var out := {}
	var ap: AnimationPlayer = p["anim"]
	var skel: Skeleton3D = p["skel"]
	for name in anim._pairs:
		var cs := float(anim._pairs[name]["contact_s"])
		var slide := 0.0
		var near := 9.0
		var prev := []
		var c := 0.0
		while c <= cs + 0.001:
			ap.play(name + "_tackler")
			ap.seek(c, true)
			var kf := []
			for f in feet:
				kf.append(skel.get_bone_global_pose(f).origin)
			var kt := []
			for b in torso:
				kt.append(skel.get_bone_global_pose(b).origin)
			ap.play(name + "_tacklee")
			ap.seek(c, true)
			var ef := []
			for f in feet:
				ef.append(skel.get_bone_global_pose(f).origin)
			for a in kt:
				for b in torso:
					near = minf(near, (a as Vector3).distance_to(skel.get_bone_global_pose(b).origin))
			var now := kf + ef
			if not prev.is_empty():
				for j in range(now.size()):
					var a2: Vector3 = prev[j]
					var b2: Vector3 = now[j]
					if a2.y < PLANTED and b2.y < PLANTED:
						slide = maxf(slide, Vector2(b2.x - a2.x, b2.z - a2.z).length() / DT)
			prev = now
			c += DT
		out[name] = {"slide": slide, "near": near}
	ap.play("idle")
	return out


func _feet(p: Dictionary, feet: Array) -> Array:
	var skel: Skeleton3D = p["skel"]
	var out := []
	for f in feet:
		out.append(skel.global_transform * skel.get_bone_global_pose(f).origin)
	return out


func _near(a: Dictionary, b: Dictionary, torso: Array) -> float:
	var sa: Skeleton3D = a["skel"]
	var sb: Skeleton3D = b["skel"]
	var best := 9.0
	for x in torso:
		var pa := sa.global_transform * sa.get_bone_global_pose(x).origin
		for y in torso:
			best = minf(best, pa.distance_to(sb.global_transform * sb.get_bone_global_pose(y).origin))
	return best


func _stats(v: Array) -> String:
	if v.is_empty():
		return "-"
	var s := v.duplicate()
	s.sort()
	return "median %.2f p90 %.2f max %.2f" % [s[s.size() / 2], s[int(s.size() * 0.9)], s[-1]]
