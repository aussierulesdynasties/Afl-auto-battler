extends SceneTree
# Turntable of manuka.glb (runtime glTF load, no import). Writes PNGs to gd_out/.
const GLB := "C:/Users/DANTE/AppData/Local/Temp/claude/42b104df8233c568/d9709e24-758e-41a6-a6a0-86482f4b0f32/scratchpad/manuka/manuka.glb"
const OUT := "C:/Users/DANTE/AppData/Local/Temp/claude/42b104df8233c568/d9709e24-758e-41a6-a6a0-86482f4b0f32/scratchpad/manuka/gd_out/"
var cam: Camera3D
func _initialize() -> void:
	var doc := GLTFDocument.new(); var st := GLTFState.new()
	var err := doc.append_from_file(GLB, st)
	if err != OK: push_error("glb load failed %d" % err); quit(1); return
	root.add_child(doc.generate_scene(st))
	var env := Environment.new(); var sky := Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.ground_bottom_color = Color(0.42,0.44,0.46); sm.ground_horizon_color = Color(0.62,0.64,0.66); sky.sky_material = sm; env.background_mode = Environment.BG_SKY; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_energy = 0.9
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var we := WorldEnvironment.new(); we.environment = env; root.add_child(we)
	var sun := DirectionalLight3D.new(); sun.shadow_enabled = true; sun.light_energy = 1.3
	sun.directional_shadow_max_distance = 700.0
	root.add_child(sun); sun.look_at_from_position(Vector3.ZERO, Vector3(0.629, -0.342, -0.698), Vector3.UP)
	cam = Camera3D.new(); cam.fov = 40.0; cam.far = 3000.0; root.add_child(cam); cam.current = true
	_run.call_deferred()
func _shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(OUT + name)
func _orbit(az: float) -> void:
	var c := Vector3(4.7, 0, 5.0); var r := 250.0
	cam.look_at_from_position(c + Vector3(cos(az) * r, 130.0, sin(az) * r), c + Vector3(0, 5, 0), Vector3.UP)
func _run() -> void:
	for i in 8: await process_frame
	cam.fov = 50.0
	cam.look_at_from_position(Vector3(68.77, 4.22, 100.77), Vector3(62.37, 3.5, 91.19), Vector3.UP)
	for i in 3: await process_frame
	await _shot("close_sign2.png")
	cam.look_at_from_position(Vector3(1.66, 6.0, 130.11), Vector3(2.1, 7.0, 112.11), Vector3.UP)
	for i in 3: await process_frame
	await _shot("close_media2.png")
	cam.look_at_from_position(Vector3(-52.0, 5.0, 124.0), Vector3(-30.0, 8.0, 106.0), Vector3.UP)
	for i in 3: await process_frame
	await _shot("close_fins.png")
	cam.look_at_from_position(Vector3(-12.0, 16.0, 70.0), Vector3(-12.0, 9.0, 93.0), Vector3.UP)
	for i in 3: await process_frame
	await _shot("close_field.png")
	quit(0)
