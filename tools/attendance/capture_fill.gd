extends SceneTree
## The 3D crowd filled to a match's attendance (MatchAttendance), for its QA sheet:
##   godot --path . --rendering-method mobile --script tools/attendance/capture_fill.gd -- OUTDIR GROUND HOME AWAY SLOT LABEL [KEY]
## Builds the ground as a match does, fills its seats to that fixture's crowd and saves
## OUTDIR/<slug>_<home><away>_<view>.png from a broadcast view, a high pocket view across the ground
## and a view of the far wing. Prints the crowd, the fill and the seats taken. Looks only.

const SIZE := Vector2i(1280, 720)
## name: [eye x, y, z, look-at x, y, z, fov] in match metres (x toward the home end).
const VIEWS := {
	"broadcast": [0.0, 32.0, 62.0, 0.0, 0.0, -30.0, 62.0],
	"pocket_high": [74.0, 16.0, 58.0, -40.0, 9.0, 100.0, 62.0],
	"far_wing": [0.0, 6.0, 20.0, 0.0, 14.0, -100.0, 70.0],
	"away_end": [-20.0, 5.0, 0.0, -110.0, 10.0, 0.0, 62.0],
}


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var ground := str(args[1])
	var home := str(args[2])
	var away := str(args[3])
	var slot := str(args[4])
	var label := str(args[5])
	var key := int(args[6]) if args.size() > 6 else 7
	DirAccess.make_dir_recursive_absolute(out)
	root.size = SIZE
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new(home, gdb.club_list(home), true, home),
			Squad_.new(away, gdb.club_list(away), false, away), 31).run()
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	oval.ground = ground
	oval.attendance = MatchAttendance.crowd(ground, home, away, slot, label, key)
	root.add_child(oval)
	oval.build(d, home, away)
	oval.turf.apply("", slot)
	oval.set_process(false)
	var crowd: Oval3DCrowd = oval.crowd
	print("ATTENDANCE %s %s v %s %s %s: %d of %d (%.0f%%), seats taken %d of %d" % [ground, home, away, slot, label,
			oval.attendance, MatchAttendance.capacity(ground), 100.0 * MatchAttendance.fill(ground, oval.attendance),
			crowd.census["taken"], crowd.census["seats"]])
	var cam: Camera3D = oval.camera
	cam.far = 3000.0
	cam.near = 0.05
	crowd.set_now(5.0)
	for i in 30:
		await process_frame
	var tag := "%s_%s%s" % [GroundModels.slug_for(ground), home.to_lower(), away.to_lower()]
	for name: String in VIEWS:
		var v: Array = VIEWS[name]
		cam.global_position = Vector3(v[0], v[1], v[2])
		cam.look_at(Vector3(v[3], v[4], v[5]), Vector3.UP)
		cam.fov = v[6]
		for i in 8:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [tag, name]))
	quit(0)
