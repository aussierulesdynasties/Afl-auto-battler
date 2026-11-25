extends SceneTree
## The MCG crowd, for its QA sheet (row 202 2c; the crowd brought up to standard, 2026-11-21):
## a match's MCG built as the game builds it, seen from views a broadcast and a supporter would
## see, and a goal's reaction filmed.
##   godot --path . --rendering-method mobile --script tools/visual/capture_mcg_crowd.gd -- OUTDIR [HOME AWAY] [bench]
## bench: no pictures; the GPU and CPU time a frame (ms, the renderer's own measure, 90 frames
## after 30 to settle) from the wing and broadcast views, to compare one build with another.
## Saves OUTDIR/<view>.png for each view and OUTDIR/goal_<n>.png, a frame every quarter second
## from a home goal. Positions are the match's metres (x along the ground toward the home end,
## +z the main camera's wing). Looks only.

const SIZE := Vector2i(1280, 720)
## name: [eye x, y, z, look-at x, y, z, fov]
const VIEWS := {
	"pocket_high": [74.0, 16.0, 58.0, -40.0, 9.0, 100.0, 62.0],
	"wing_close": [0.0, 3.0, 72.0, 25.0, 12.0, 100.0, 60.0],
	"home_end": [30.0, 4.0, 0.0, 110.0, 8.0, 0.0, 55.0],
	"away_end": [-30.0, 4.0, 0.0, -110.0, 8.0, 0.0, 55.0],
	"members": [0.0, 4.0, 0.0, -70.0, 12.0, -85.0, 60.0],
	"broadcast": [0.0, 32.0, 62.0, 0.0, 0.0, -30.0, 62.0],
}
const GOAL_VIEW := [8.0, 3.0, 70.0, 30.0, 11.0, 100.0, 58.0]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var home := str(args[1]) if args.size() > 1 else "COL"
	var away := str(args[2]) if args.size() > 2 else "ESS"
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
	oval.ground = "MCG"
	root.add_child(oval)
	oval.build(d, home, away)
	oval.set_process(false)
	var crowd: Oval3DCrowd = oval.crowd
	print("CROWD ", crowd.supporters, " ", crowd.census)
	var cam: Camera3D = oval.camera
	cam.far = 3000.0
	cam.near = 0.05
	crowd.set_now(5.0)
	if "bench" in args:
		var vp := root.get_viewport().get_viewport_rid()
		RenderingServer.viewport_set_measure_render_time(vp, true)
		for name in ["wing_close", "broadcast"]:
			_aim(cam, VIEWS[name])
			var gpu := 0.0
			var cpu := 0.0
			for i in 120:
				crowd.set_now(5.0 + i / 30.0)
				await process_frame
				if i >= 30:
					gpu += RenderingServer.viewport_get_measured_render_time_gpu(vp)
					cpu += RenderingServer.viewport_get_measured_render_time_cpu(vp)
			print("BENCH %s gpu %.2f cpu %.2f ms" % [name, gpu / 90.0, cpu / 90.0])
		quit(0)
		return
	for name: String in VIEWS:
		_aim(cam, VIEWS[name])
		for i in 8:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
	# A home goal at 10 s: the home supporters rise, a beat apart; a few away hold their heads.
	_aim(cam, GOAL_VIEW)
	crowd.cheer(0, 10.0)
	for f in range(17):
		crowd.set_now(9.75 + f * 0.25)
		for i in 3:
			await process_frame
		root.get_viewport().get_texture().get_image().save_png(out.path_join("goal_%02d.png" % f))
	quit(0)


func _aim(cam: Camera3D, v: Array) -> void:
	cam.global_position = Vector3(v[0], v[1], v[2])
	cam.look_at(Vector3(v[3], v[4], v[5]), Vector3.UP)
	cam.fov = v[6]
