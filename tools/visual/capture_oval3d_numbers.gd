extends SceneTree
## Guernsey numbers as the TV shows them (row 202 2d): every club's current guernsey, backs to
## the lens, on the main broadcast camera, the set shot camera (behind the kicker) and a close
## cut, at each graphics level (Oval3DQuality) on a normal and a narrow phone's 3D picture.
##   godot --path . --rendering-method mobile --script tools/visual/capture_oval3d_numbers.gd -- OUTDIR [--only=main,close]
## Each frame is saved whole (<shot>_<phone>_<level>.png) and the players' patch of it is cut out
## and blown up 4x without smoothing (crop_<...>.png), so each picture pixel is seen as drawn.

## Every club with a current guernsey (data/kits_today.csv), each with a number that tests
## something: one digit, two alike, wide and narrow pairs.
const CLUBS := ["ADE", "BRL", "CAR", "COL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW",
		"MEL", "NTH", "PAD", "RIC", "STK", "SYD", "CANB", "TAS", "WCE", "WBD"]
const NUMBERS := [9, 11, 35, 4, 18, 23, 7, 44, 1, 26, 8, 30, 17, 12, 6, 37, 3, 22, 40, 5]
const COLS := 10
const GAP := 1.5
const ROW_GAP := 12.0   # m between the two rows, so the front row never hides the back's numbers
## A phone's 3D picture in screen pixels (PitchView draws at the screen's own pixels): the oval
## gets about 2.2 of 3.2 of the match body's height under the header. Normal: a 390 dp phone at
## 2.75x; narrow: a 360 dp phone at 2x.
const PHONES := {"normal": Vector2i(1072, 1290), "narrow": Vector2i(720, 870)}
const LEVELS := ["high", "medium", "low"]
const KICK_FROM := 45.0  # m out from goal, a set shot


func _initialize() -> void:
	_run.call_deferred()
	create_timer(600.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_numbers"
	var only := []
	for a in args:
		if str(a).begins_with("--only="):
			only = str(a).substr(7).split(",")
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval._environment()
	oval._ground()
	var scene: PackedScene = load(oval.PLAYER_GLB)
	var figs := []
	for i in range(CLUBS.size()):
		var code: String = CLUBS[i]
		var p: Dictionary = oval._player(scene, oval._kit(gdb.club_guernsey(code)), gdb.club_colours(code), code)
		oval._number(p, NUMBERS[i])
		(p["anim"] as AnimationPlayer).advance(1e-4)
		figs.append(p["node"])
	var B = load("res://scripts/ui/match/Oval3DBroadcast.gd")
	var Q = load("res://scripts/ui/match/Oval3DQuality.gd")
	var cam := Camera3D.new()
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	cam.far = 2000.0
	root.add_child(cam)
	cam.make_current()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	var fwd := _facing(figs[0])
	var half_len: float = load("res://scripts/ui/match/MatchMotion.gd").HALF_LEN
	for shot in ["main", "setshot", "close"]:
		if not only.is_empty() and not shot in only:
			continue
		# Where the men stand and where the lens is, for this shot.
		var eye: Vector3
		var aim: Vector3
		var width: float
		var centre := Vector3.ZERO
		if shot == "main":
			eye = B.main_eye()
			centre = Vector3(0.0, 0.0, 0.0)
			aim = centre + Vector3(0.0, B.AIM_Y, 0.0)
			width = B.MAIN_WIDTH
		elif shot == "setshot":
			# Kicking at the -x goals from 45 m out; the goals camera behind the far (+x) goals.
			eye = Vector3(half_len + B.EYE_BACK, B.EYE_UP, 0.0)
			centre = Vector3(-half_len + KICK_FROM, 0.0, 0.0)
			aim = Vector3(-half_len, B.GOALS_AIM_Y, 0.0)
			width = B.GOALS_WIDTH
		else:
			centre = Vector3(0.0, 0.0, 0.0)
			aim = Vector3(0.0, B.CLOSE_AIM_Y, 0.0)
			eye = aim + Vector3(0.0, 0.6, 7.0)
			width = B.CLOSE_WIDTH
		_place(figs, centre, eye, fwd, shot == "close")
		for phone in PHONES:
			var sz: Vector2i = PHONES[phone]
			root.size = sz
			DisplayServer.window_set_size(sz)
			for level in LEVELS:
				Q.apply_viewport(level, root)
				Q.apply_shadows(level)
				Q.apply_sun(level, oval._sun)
				cam.global_position = eye
				cam.look_at(aim, Vector3.UP)
				cam.fov = rad_to_deg(2.0 * atan(width * 0.5 / eye.distance_to(aim)))
				if shot == "main":
					# Oval3DBroadcast._tv_height: the TV picture's height fills the phone's taller picture.
					var tw := tan(deg_to_rad(cam.fov) * 0.5)
					cam.fov = rad_to_deg(2.0 * atan(tw * 9.0 / 16.0 * float(sz.x) / float(sz.y)))
				for k in range(6):
					await process_frame
				await RenderingServer.frame_post_draw
				var img: Image = root.get_viewport().get_texture().get_image()
				var name := "%s_%s_%s" % [shot, phone, level]
				img.save_png(out.path_join(name + ".png"))
				_crop(img, cam, figs, out.path_join("crop_" + name + ".png"), shot == "close")
				print("SAVED ", name)
	print("DONE ", out)
	quit()


## The men in a block at centre, backs to the eye (the close cut: one man, the rest away).
func _place(figs: Array, centre: Vector3, eye: Vector3, fwd: Vector3, one: bool) -> void:
	var to_eye := Vector3(eye.x - centre.x, 0.0, eye.z - centre.z).normalized()
	var across := to_eye.cross(Vector3.UP).normalized()
	var rows := int(ceil(float(figs.size()) / COLS))
	for i in range(figs.size()):
		var nd: Node3D = figs[i]
		var r := i / COLS
		var c := i % COLS
		nd.position = centre + across * (c - (COLS - 1) * 0.5) * GAP - to_eye * (r - (rows - 1) * 0.5) * ROW_GAP
		# The chest faces fwd at rest; turn him so the chest points away from the lens.
		nd.rotation.y = 0.0
		var ang := Vector2(fwd.x, fwd.z).angle_to(Vector2(-to_eye.x, -to_eye.z))
		nd.rotation.y = -ang
		if one:
			nd.visible = i == 13   # Richmond: the edged number
			nd.position = centre if i == 13 else nd.position + Vector3(0, -50, 0)


## The men's patch of the frame, blown up 4x pixel for pixel.
func _crop(img: Image, cam: Camera3D, figs: Array, path: String, one: bool) -> void:
	var lo := Vector2(1e9, 1e9)
	var hi := Vector2(-1e9, -1e9)
	for nd: Node3D in figs:
		if not nd.visible:
			continue
		for h in [Vector3(-0.5, 0.0, -0.5), Vector3(0.5, 2.0, 0.5)]:
			var p := cam.unproject_position(nd.global_position + h)
			lo = lo.min(p)
			hi = hi.max(p)
	var scale := float(img.get_width()) / float(root.size.x)
	var pad := 8.0
	var r := Rect2i(Vector2i((lo - Vector2(pad, pad)) * scale), Vector2i((hi - lo + Vector2(pad, pad) * 2.0) * scale))
	r = r.intersection(Rect2i(Vector2i.ZERO, img.get_size()))
	if r.size.x <= 0 or r.size.y <= 0:
		return
	var c := img.get_region(r)
	if not one:
		c.resize(c.get_width() * 4, c.get_height() * 4, Image.INTERPOLATE_NEAREST)
	c.save_png(path)


## The direction the rest pose's chest faces (capture_oval3d_kits._facing).
func _facing(fig: Node3D) -> Vector3:
	var mi: MeshInstance3D = fig.find_children("*", "MeshInstance3D", true, false)[0]
	var arr: Array = mi.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var uv2: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV2]
	var front := Vector3.ZERO
	var back := Vector3.ZERO
	var nf := 0
	var nb := 0
	for k in range(verts.size()):
		if uv2[k].y < 0.1 and verts[k].y > 1.0:
			front += verts[k]; nf += 1
		elif uv2[k].y > 0.9 and verts[k].y > 1.0:
			back += verts[k]; nb += 1
	var d := (front / maxf(1, nf) - back / maxf(1, nb))
	d.y = 0.0
	return (mi.global_transform.basis * d).normalized()
