extends SceneTree
## How much the 3D players' feet slide on the turf (row 198, "no skating"):
##   godot --headless --path . --script tools/visual/measure_oval3d_feet.gd -- [SECONDS] [SEED] [mh|avg]
## Fremantle v St Kilda (seed 31 unless given) played through MatchDirector at 60 frames a
## second on the MetaHuman body (mh, the default) or the old one (avg). Every frame, for every
## man not in a two-man take or a scoop: each foot on the ground (its ball bone within PLANTED
## of the lowest that foot gets in the run loop) and how fast it moves across the turf. A foot on
## the ground should not move at all; a real stride slides a few centimetres a step at most.
## Prints the planted feet's speeds by what he is doing (running, standing, easing between them,
## turning hard) and a summary line SKATE (share of planted-foot frames sliding faster than
## SKATE_AT) a test or a PR can quote.

const DT := 1.0 / 60.0
const PLANTED := 0.03          # m above the foot's lowest in the run loop: on the ground
const SKATE_AT := 0.5          # m/s: a planted foot sliding faster than this reads as skating
const FEET := ["ball_l", "ball_r"]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var secs := float(args[0]) if args.size() > 0 else 300.0
	var seed := int(args[1]) if args.size() > 1 else 31
	var body := str(args[2]) if args.size() > 2 else "mh"
	var O = load("res://scripts/ui/match/Oval3D.gd")
	if body == "mh":
		O.player_glb = "res://assets/oval3d/player_mh.glb"
		O.loops_glb = "res://assets/oval3d/player_mh.glb"
	elif body == "avg":
		O.player_glb = "res://assets/oval3d/player_average.glb"
		O.loops_glb = "res://assets/oval3d/player_loops.glb"
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), seed).run()
	res["home"] = "FRE"
	res["away"] = "STK"
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = O.new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var anim = oval.anim
	var skel0: Skeleton3D = oval.players[0]["skel"]
	var feet := []
	for f in FEET:
		feet.append(skel0.find_bone(f))
	var floor_y := _floor(oval.players[0], feet)
	print("BODY %s | foot floor l %.3f r %.3f m | jog loop speed %.2f m/s" % [body, floor_y[0], floor_y[1],
			float(anim.loop_speed("jog", oval.players[0])) if anim.has_method("loop_speed") else O.LOOP_SPEED])
	var by := {}                # state -> speeds of planted feet
	var rates := []             # the running clip's rate, frame by frame
	var last := {}              # player -> [left, right] world positions last frame
	var yaw_last := {}
	var at_last := {}           # player -> his node's ground spot last frame
	var drawn := []             # how fast the men are drawn moving, m/s (not standing)
	var t := 0.0
	while t < secs:
		d.advance(DT)
		oval.sync(DT)
		t += DT
		for j in range(oval.players.size()):
			var pj: Dictionary = oval.players[j]
			if not (anim._in[j] as Dictionary).is_empty() or not (anim._once[j] as Dictionary).is_empty():
				last.erase(j)
				at_last.erase(j)
				continue
			var node: Node3D = pj["node"]
			var now := _feet(pj, feet)
			var here := Vector2(node.position.x, node.position.z)
			if at_last.has(j):
				var v := here.distance_to(at_last[j]) / DT
				if v > 0.5:
					drawn.append(v)
			at_last[j] = here
			var yaw := node.rotation.y
			var cur := (pj["anim"] as AnimationPlayer).current_animation
			var state := cur
			if not (anim._blend[j] as Dictionary).is_empty():
				state = "easing"
			if yaw_last.has(j) and absf(wrapf(yaw - float(yaw_last[j]), -PI, PI)) / DT > 3.0:
				state = "turning"
			if cur in ["jog", "carry"] and float(anim._rate[j]) > 0.0:
				rates.append(float(anim._rate[j]))
			if last.has(j):
				for f in range(2):
					var a: Vector3 = last[j][f]
					var b: Vector3 = now[f]
					if a.y - node.global_position.y < floor_y[f] + PLANTED and b.y - node.global_position.y < floor_y[f] + PLANTED:
						var key := state
						if OS.get_environment("FEET_DEBUG") != "" and "_feet" in anim:
							var lk: Dictionary = anim._feet[j][f]
							key += "/" + ("free" if lk.is_empty() else ("step" if float(lk["step"]) >= 0.0 else ("held" if float(lk["w"]) >= 1.0 else "letgo")))
						if not by.has(key):
							by[key] = []
						by[key].append(Vector2(b.x - a.x, b.z - a.z).length() / DT)
			last[j] = now
			yaw_last[j] = yaw
	var all := []
	for s in by:
		all.append_array(by[s])
		print("  %-8s %s" % [s, _stats(by[s])])
	print("  rates   %s" % _stats(rates))
	print("  drawn   %s m/s" % _stats(drawn))
	var skate := 0
	for v in all:
		skate += 1 if float(v) > SKATE_AT else 0
	print("SKATE %s %.1f%% of %d planted-foot frames over %.1f m/s | all %s" % [body,
			100.0 * skate / maxf(1.0, all.size()), all.size(), SKATE_AT, _stats(all)])
	quit()


## Each foot's lowest height in the run loop, in the figure's own space.
func _floor(p: Dictionary, feet: Array) -> Array:
	var ap: AnimationPlayer = p["anim"]
	var skel: Skeleton3D = p["skel"]
	var lo := [INF, INF]
	ap.play("jog")
	var n := 60
	for k in range(n + 1):
		ap.seek(ap.current_animation_length * k / n, true)
		for f in range(2):
			var y := (skel.global_transform * skel.get_bone_global_pose(feet[f]).origin).y \
					- (p["node"] as Node3D).global_position.y
			lo[f] = minf(lo[f], y)
	ap.play("idle")
	return lo


func _feet(p: Dictionary, feet: Array) -> Array:
	var skel: Skeleton3D = p["skel"]
	var out := []
	for f in feet:
		out.append(skel.global_transform * skel.get_bone_global_pose(f).origin)
	return out


func _stats(a: Array) -> String:
	if a.is_empty():
		return "n 0"
	var s := a.duplicate()
	s.sort()
	var sum := 0.0
	for v in s:
		sum += float(v)
	return "n %d mean %.2f p50 %.2f p90 %.2f p99 %.2f max %.2f" % [s.size(), sum / s.size(),
			float(s[s.size() / 2]), float(s[int(s.size() * 0.9)]), float(s[int(s.size() * 0.99)]), float(s[-1])]
