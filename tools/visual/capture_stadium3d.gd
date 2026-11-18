extends SceneTree
## Stills of each ground's 3D stadium (row 202, 3D view plan 2b), for the director's boards.
##   godot --windowed --path . --script tools/visual/capture_stadium3d.gd -- OUTDIR "MCG" "Adelaide Oval" ...
## Fremantle v St Kilda (seed 31) 30 s in, on a fine day (rules 2.80-2.81's look). For each ground:
##   main   the main camera (rule 2.93: centre line, 15 m up, 25 m back), wide to the far stand
##   high   high over the near wing's stand, the whole ground in view
##   end    behind a goal, high in the end stand
##   goal   low behind a goal, along the fence boards (a test view, not a game camera)
## FENCE=plain|sponsor|club sets the fence boards' look (Oval3DStadium.fence_look) and names the files
## OUTDIR/<ground>_<shot>_<look>.png.
## Files: OUTDIR/<ground>_<shot>.png (spaces become _). Prints each ground's supporters.

const DT := 1.0 / 120.0
const SHOTS := {
	"main": [Vector3(0.0, 15.0, 92.4), Vector3(0.0, 4.0, -40.0), 120.0],
	"high": [Vector3(60.0, 120.0, 230.0), Vector3(0.0, 0.0, 0.0), 420.0],
	"end": [Vector3(-118.0, 30.0, 0.0), Vector3(20.0, 0.0, 0.0), 240.0],
	"goal": [Vector3(-101.0, 6.0, 8.0), Vector3(-40.0, 1.0, -30.0), 70.0],
}
var _clouds: NoiseTexture2D


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1800.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	root.size = Vector2i(1280, 720)
	DisplayServer.window_set_size(root.size)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	var look := OS.get_environment("FENCE")
	if look != "":
		load("res://scripts/ui/match/Oval3DStadium.gd").fence_look = look
	_make_clouds()
	await _clouds.changed
	for gi in range(1, args.size()):
		var ground := str(args[gi])
		load("res://scripts/ui/match/VignetteGround.gd").venue = ground
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var t0 := Time.get_ticks_msec()
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		root.add_child(oval)
		oval.build(d, "FRE", "STK")
		print("GROUND %s: %d supporters, built in %d ms" % [ground, oval.crowd.supporters, Time.get_ticks_msec() - t0])
		_look(oval)
		for n in range(int(30.0 / DT)):
			d.advance(DT)
			oval.sync(DT)
		var cam: Camera3D = oval.camera
		cam.far = 2000.0
		for shot in SHOTS:
			var s: Array = SHOTS[shot]
			await _expose(oval, cam, s[0], s[1], s[2])
			var img := root.get_viewport().get_texture().get_image()
			img.save_png(out.path_join("%s_%s%s.png" % [ground.replace(" ", "_").replace("'", ""), shot,
					("_" + look) if look != "" else ""]))
		oval.queue_free()
		await process_frame
	quit(0)


func _expose(oval, cam: Camera3D, eye: Vector3, aim: Vector3, width: float) -> void:
	cam.global_position = eye
	cam.look_at(aim, Vector3.UP)
	cam.fov = minf(80.0, rad_to_deg(2.0 * atan(width * 0.5 / eye.distance_to(aim))))
	var env: Environment = oval._env
	for it in range(3):
		for w in range(3):
			await process_frame
		await RenderingServer.frame_post_draw


func _make_clouds() -> void:
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_PERLIN
	fn.fractal_type = FastNoiseLite.FRACTAL_FBM
	fn.fractal_octaves = 5
	fn.frequency = 0.008
	fn.seed = 7
	_clouds = NoiseTexture2D.new()
	_clouds.width = 512
	_clouds.height = 512
	_clouds.seamless = true
	_clouds.generate_mipmaps = true
	_clouds.noise = fn


## Rule 2.80 (sky light, a fine day) and 2.81 (AgX, contrast 1.1, saturation 1.2), as
## capture_cameras3d.gd sets them.
func _look(oval) -> void:
	var env: Environment = oval._env
	oval.turf.apply("perfect", "day")
	var sm := ShaderMaterial.new()
	sm.shader = load("res://tools/visual/look3d_sky.gdshader")
	sm.set_shader_parameter("energy", 1.4)
	sm.set_shader_parameter("clouds_tex", _clouds)
	sm.set_shader_parameter("cover", 0.32)
	sm.set_shader_parameter("cloud_lit", Color(1, 1, 1))
	sm.set_shader_parameter("cloud_dark", Color(0.62, 0.66, 0.74))
	sm.set_shader_parameter("sun_halo", 0.35)
	var sky := Sky.new()
	sky.sky_material = sm
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_sky_contribution = 1.0
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	oval._sun.light_energy = 1.15
	oval._sun.light_color = Color(1.0, 0.95, 0.86)
	oval._sun.directional_shadow_max_distance = 400.0
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.0
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.1
	env.adjustment_saturation = 1.2
	var hz: Color = RenderingServer.shader_get_parameter_default(sm.shader.get_rid(), "horizon")
	var lum := 0.2126 * hz.r + 0.7152 * hz.g + 0.0722 * hz.b
	sm.set_shader_parameter("view", 0.75 / (env.tonemap_exposure * 1.4 * lum))
