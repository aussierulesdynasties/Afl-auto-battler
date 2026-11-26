extends SceneTree
## The broadcast cameras' mounts in each ground's background-scene frame (scene metres: x east, y north, z up), for
## reduce.py BG_CAMS: no scene tree crown within 25 m of one. The ground's backdrop must be installed (its transform).
## usage: xvfb-run -a godot --path . --rendering-method mobile --script tools/grounds/backdrop/broadcast_cams.gd -- <slug> ...
## prints "CAMS <slug> [[x, y, z], ...]" per ground; collect into scene/broadcast_cams.json

const L := 86.3   # MatchMotion.HALF_LEN
const W := 67.4   # MatchMotion.HALF_WID


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


## [name, eye, aim, width across the picture at the aim (m) or a field of view (degrees, < 0)].
func _shots() -> Array:
	var b = load("res://scripts/ui/match/Oval3DBroadcast.gd")
	var eye: Vector3 = b.main_eye()
	var up: float = b.EYE_UP
	var back: float = b.EYE_BACK
	var w50: float = b.wing_50()
	return [
		["main_far_wing", eye, Vector3(0, 1, -W), 57.0],
		["main_wide", eye, Vector3(0, 1, -W * 0.3), 150.0],
		["main_left_pocket", eye, Vector3(-L + 10, 1, -W * 0.6), 57.0],
		["main_right_pocket", eye, Vector3(L - 10, 1, -W * 0.6), 57.0],
		["wing50_left", eye + Vector3(-w50, 0, 0), Vector3(-L, 1, -20), 60.0],
		["wing50_right", eye + Vector3(w50, 0, 0), Vector3(L, 1, -20), 60.0],
		["goals_left", Vector3(L + back, up, 0), Vector3(-L, 3.3, 0), 42.0],
		["goals_right", Vector3(-(L + back), up, 0), Vector3(L, 3.3, 0), 42.0],
		["outside_city", Vector3(260, 90, 420), Vector3(-200, 30, -400), -55.0],
		["outside_park", Vector3(-420, 140, 380), Vector3(0, 0, 0), -50.0],
		["outside_high", Vector3(0, 650, 900), Vector3(0, 0, 0), -50.0],
	]


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("COL", gdb.club_list("COL"), true, "COL"),
			Squad_.new("CAR", gdb.club_list("CAR"), false, "CAR"), 31).run()
	for slug in args:
		var g := ""
		for name in GroundModels.grounds():
			if GroundModels.slug_for(name) == slug:
				g = name
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = g
		root.add_child(oval)
		oval.build(d, "COL", "CAR")
		oval.set_process(false)
		await process_frame
		var bds: Array = oval.find_children("Backdrop", "", true, false)
		if bds.is_empty():
			print("CAMS ", slug, " none")
		else:
			var inv: Transform3D = (bds[0] as Node3D).global_transform.affine_inverse()
			var pts := []
			for s in _shots().slice(0, 8):
				var l: Vector3 = inv * (s[1] as Vector3)
				pts.append([snappedf(l.x, 0.1), snappedf(-l.z, 0.1), snappedf(l.y, 0.1)])
			print("CAMS ", slug, " ", JSON.stringify(pts))
		oval.queue_free()
		await process_frame
	quit()
