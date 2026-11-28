extends "res://tools/visual/capture_look3d.gd"
## PROTOTYPE (row 202, close-up supporters): one candidate supporter in our stand, filmed from the
## row behind with the ground beyond (the director's shot: "a supporter's head and shoulders in
## the foreground"). Nothing here is the game's until he picks it.
##   godot --path . --script tools/visual/capture_closeup3d.gd -- OUTDIR FIGURE.glb CLIP HEIGHT_M [FRAMES]
## FIGURE: a GLB (res:// or an absolute path) with CLIP among its animations. HEIGHT_M: his standing
## height. FRAMES: frames to film at 24 fps (1 = a still).
## The match moment: 2 s after the first goal of the seeded Fremantle v St Kilda match (a break in play).
## Env: ROW (default 8) the supporter's row; SIDE (default 0.45) m the camera sits off his right
## shoulder; BACK (default 1.25) m behind him; EYE (default 1.62) camera height over his tread;
## FOV (default 50); TURN (default 0) deg the camera looks away from straight across the ground;
## WING (default 0 = the wing nearest the play) 1 or -1 picks a wing.
## HAIRMODE scissor | prepass | hash (default). ALLMIPS=1 gives every texture mipmaps (a GLB read at run time has
## none, so skin pores speckle); LASHRAW=1 leaves the lashes without (mipmaps fade them away); SS=2 draws the
## 3D at twice the resolution and shrinks it, so sub-pixel lashes read as fine hairs. MSAA=2|4|8.
## Skin: SKINNORM (pore bump strength, 0.5 softens the speckle), SKINROUGH, SKINSPEC (sheen), SKINSSS (light
## through the skin), SKINCULL=1 one-sided. SHADOWRES=8192 SHADOWBLUR SHADOWDIST: a finer, softer sun shadow (its
## jagged edge read as speckle on her cheek). STANDBOUNCE=E lights her from below with the stand's colour (x E) instead of
## the turf's green. HIDE=SUP_eye,SUP_lash hides those surfaces (fault hunting).
## SCARF / BEANIE: comma-separated club colours for the knitwear (SupporterMerch).

const AFTER_GOAL := 2.0


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0])
	var fig_path := str(args[1])
	var clip := str(args[2])
	var height := float(args[3])
	var frames := int(args[4]) if args.size() > 4 else 1
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var Sim = load("res://scripts/sim/MatchSim.gd")
	var res: Dictionary = Sim.new(Squad_.new("FRE", gdb.club_list("FRE"), true, "FRE"),
			Squad_.new("STK", gdb.club_list("STK"), false, "STK"), 31).run()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.use_debanding = true
	_size(WIDE)
	var d = load("res://scripts/ui/match/MatchDirector.gd").new()
	d.setup(res, res["events"])
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval.build(d, "FRE", "STK")
	var played := 0.0
	var goal_t := -1.0
	while played < MAX_T:
		d.advance(DT)
		oval.sync(DT)
		oval.aim_end(UP, BACK)
		played += DT
		if goal_t < 0.0 and played > 6.0 and not d.flash.is_empty() and bool(d.flash.get("goal", false)):
			goal_t = played
		if goal_t >= 0.0 and played >= goal_t + AFTER_GOAL:
			break
		await process_frame
	print("CLOSEUP goal at %.2f s, filming from %.2f s" % [goal_t, played])
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
	await _clouds.changed
	_reset(oval, "perfect", "day")
	for part in ["sky", "agxtv"]:
		_apply(oval, part)
	await _match_exposure(oval)
	if OS.has_environment("STANDBOUNCE"):   # she sits in the stand: the light from below is the stand's, not the turf's green
		var skm = oval._env.sky.sky_material if oval._env.sky != null else null
		if skm is ShaderMaterial:
			var bowl = skm.get_shader_parameter("bowl")   # unset = the shader's default stand colour
			skm.set_shader_parameter("grass", bowl if bowl != null else Color(0.22, 0.21, 0.23))
			skm.set_shader_parameter("grass_energy", _env("STANDBOUNCE", 1.0))
	if OS.has_environment("SS"):   # supersample: draw the 3D at SS x the resolution and shrink it
		oval.get_viewport().scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
		oval.get_viewport().scaling_3d_scale = float(OS.get_environment("SS"))
	if OS.has_environment("SHADOWRES"):   # the sun's shadow drawn finer and softened (a jagged edge reads as speckle on skin)
		RenderingServer.directional_shadow_atlas_set_size(int(OS.get_environment("SHADOWRES")), true)
		for l in oval.find_children("*", "DirectionalLight3D", true, false):
			(l as DirectionalLight3D).shadow_blur = _env("SHADOWBLUR", 1.0)
			(l as DirectionalLight3D).directional_shadow_max_distance = _env("SHADOWDIST", 20.0)
	if OS.has_environment("MSAA"):   # the look-test reset turns MSAA off; MSAA=2|4|8 puts it back
		oval.get_viewport().msaa_3d = {"2": Viewport.MSAA_2X, "4": Viewport.MSAA_4X, "8": Viewport.MSAA_8X}[OS.get_environment("MSAA")]
	# The seat: ROW rows up the stand on the wing nearest the play, square to the centre line.
	var O = oval.get_script()
	var C = Oval3DCrowd
	var pitch: float = O.STAND_DEPTH / C.ROWS
	var rise: float = (O.STAND_RISE - C.BASE_Y) / C.ROWS
	var row := int(_env("ROW", 8.0))
	var dd: float = row * pitch + C.PERSON_D
	var y: float = C.BASE_Y + (row + 1) * rise
	var zs := -1.0 if oval.ball.global_position.z < 0.0 else 1.0
	if _env("WING", 0.0) != 0.0:
		zs = signf(_env("WING", 0.0))
	var seat := Vector3(oval.ball.global_position.x * 0.0, y, zs * (O.HALF_WID + O.FENCE + dd))
	var inward := Vector3(0, 0, -zs)
	# Empty the seats between the camera and him, and his neighbours, so nothing of today's crowd
	# stands in the foreground but him.
	_clear_seat(oval, seat, _env("CLEAR", 2.6))
	var fig := _load_figure(fig_path)
	oval.add_child(fig)
	var aabb := _aabb(fig)
	var k := height / maxf(0.01, aabb.size.y)
	fig.scale = Vector3.ONE * k
	fig.global_position = seat - Vector3(0, aabb.position.y * k, 0)
	fig.look_at(fig.global_position - inward, Vector3.UP)   # -Z away from the ground: the body's +Z faces in
	# Mixamo's materials import glossy (wet-looking cloth and skin): matte them.
	for m in fig.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (m as MeshInstance3D).mesh
		for si in mesh.get_surface_count():
			var mat := mesh.surface_get_material(si)
			if mat is BaseMaterial3D:
				if OS.has_environment("ALLMIPS"):   # a GLB read at run time has no mipmaps: fine detail (pores) aliases to speckle
					for slot in [BaseMaterial3D.TEXTURE_ALBEDO, BaseMaterial3D.TEXTURE_NORMAL, BaseMaterial3D.TEXTURE_ROUGHNESS, BaseMaterial3D.TEXTURE_METALLIC, BaseMaterial3D.TEXTURE_AMBIENT_OCCLUSION]:
						var tx: Texture2D = mat.get_texture(slot)
						if tx != null and tx.get_image() != null and not tx.get_image().has_mipmaps() and not (OS.has_environment("LASHRAW") and mat.resource_name == "SUP_lash"):
							var ti := tx.get_image()
							if ti.is_compressed(): ti.decompress()
							ti.generate_mipmaps()
							mat.set_texture(slot, ImageTexture.create_from_image(ti))
				# Mixamo's roughness map multiplies the value down to wet shine: drop it.
				mat.roughness_texture = null
				mat.roughness = 0.9
				mat.metallic = 0.0
				mat.metallic_texture = null
				mat.metallic_specular = 0.2
				if mat.resource_name in ["SUP_head", "SUP_body"]:   # skin look tests
					if OS.has_environment("SKINCULL"): mat.cull_mode = BaseMaterial3D.CULL_BACK   # the GLB marks skin two-sided
					if OS.has_environment("SKINNORM"): mat.normal_scale = float(OS.get_environment("SKINNORM"))
					if OS.has_environment("SKINROUGH"): mat.roughness = float(OS.get_environment("SKINROUGH"))
					if OS.has_environment("SKINSPEC"): mat.metallic_specular = float(OS.get_environment("SKINSPEC"))
					if OS.has_environment("SKINSSS"):
						mat.subsurf_scatter_enabled = true
						mat.subsurf_scatter_strength = float(OS.get_environment("SKINSSS"))
						mat.subsurf_scatter_skin_mode = true
				if OS.has_environment("HIDE") and mat.resource_name in OS.get_environment("HIDE").split(","):
					mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					mat.albedo_color.a = 0.0
				# Hair cards: cut out by their alpha and drawn from both sides.
				var tex: Texture2D = mat.albedo_texture
				if tex != null and tex.get_image() != null and tex.get_image().detect_alpha() != Image.ALPHA_NONE:
					match OS.get_environment("HAIRMODE"):
						"prepass": mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
						"scissor":
							mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
							mat.alpha_scissor_threshold = float(OS.get_environment("HAIRCUT")) if OS.has_environment("HAIRCUT") else 0.3
						_: mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
					mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	# Knitwear in club colours: SCARF="#hex,#hex[,..]" BEANIE="#hex,#hex" (any club, Forge clubs too).
	if OS.has_environment("SCARF"):
		var bc := OS.get_environment("BEANIE") if OS.has_environment("BEANIE") else OS.get_environment("SCARF")
		print("CLOSEUP knitwear dressed: ", SupporterMerch.dress(fig, Array(OS.get_environment("SCARF").split(",")),
				Array(bc.split(","))))
	var ap := _anim_player(fig)
	if ap != null and ap.has_animation(clip):
		ap.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
		# Stepped by hand, one film frame (DT) per saved frame: the clip keeps its real speed however long a save takes.
		ap.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		ap.play(clip)
	print("CLOSEUP figure %s: %.2f m tall unscaled, scale %.3f, clip %s (%s)" % [fig_path, aabb.size.y, k,
			clip, "playing" if ap != null and ap.has_animation(clip) else "MISSING"])
	var right := inward.cross(Vector3.UP)
	var cam: Camera3D = oval.camera
	cam.fov = _env("FOV", 50.0)
	cam.near = 0.05
	var eye := seat - inward * _env("BACK", 1.25) + right * _env("SIDE", 0.45) + Vector3(0, _env("EYE", 1.62), 0)
	cam.global_position = eye
	var tgt := eye + inward.rotated(Vector3.UP, deg_to_rad(_env("TURN", 0.0))) * 60.0
	tgt.y = 0.0
	cam.look_at(tgt, Vector3.UP)
	for i in range(frames):
		d.advance(DT)
		oval.sync(DT)
		if ap != null and ap.is_playing():
			ap.advance(DT if i > 0 else 0.0)
		# sync aims the camera at the play: put ours back.
		cam.global_position = eye
		cam.look_at(tgt, Vector3.UP)
		await process_frame
		await _save(oval, out, "f_%04d" % i)
	quit()


func _env(n: String, dflt: float) -> float:
	var v := OS.get_environment(n)
	return float(v) if v != "" else dflt


func _load_figure(p: String) -> Node3D:
	if p.begins_with("res://"):
		return (load(p) as PackedScene).instantiate()
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(p, st)
	assert(err == OK, "could not read " + p)
	return doc.generate_scene(st)


func _anim_player(n: Node) -> AnimationPlayer:
	if n is AnimationPlayer:
		return n
	for c in n.get_children():
		var a := _anim_player(c)
		if a != null:
			return a
	return null


func _aabb(n: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		# Skinned: drawn by the skeleton's bones, so the mesh's own AABB is the body in metres
		# (Mixamo's Armature node carries a 0.01 scale its bones undo).
		var b := mi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box


## Empty the crowd's seats round p (the candidate takes that seat).
func _clear_seat(oval, p: Vector3, r: float) -> void:
	for mmi in oval.crowd.find_children("*", "MultiMeshInstance3D", true, false):
		var mm: MultiMesh = mmi.multimesh
		for i in range(mm.instance_count):
			var t := mm.get_instance_transform(i)
			if Vector2(t.origin.x - p.x, t.origin.z - p.z).length() < r and absf(t.origin.y - p.y) < 2.0:
				mm.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * 0.0001), t.origin))
