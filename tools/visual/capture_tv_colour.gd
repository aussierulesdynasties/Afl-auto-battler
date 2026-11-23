extends SceneTree
## The 3D oval's colour against real broadcast colour (row 202, the TV tone): one moment of a
## match from the game's TV main camera (Oval3DBroadcast) at each ground, under each time of day,
## with the film's broadcast colour off (rule 2.81 as approved) and on.
##   godot --path . --rendering-method mobile --script tools/visual/capture_tv_colour.gd -- OUTDIR [GROUND ...]
## Saves OUTDIR/<slug>_<slot>_<off|on>.png and prints the average colour of the open grass (the
## lower part of the picture, players and markings left out) and of a grey card standing on the
## turf in open light, in 0-255 sRGB: what a photo of the same spot would be measured with.

const SIZE := Vector2i(720, 1280)
const SLOTS := ["day", "twilight", "night"]
const DT := 1.0 / 30.0
const AT := 14.0
const CALIBRATE := 5
## `calibrate` in the arguments: find each look's white balance from the card instead of using
## Oval3DTurf.BALANCE's.
var calibrate := false
## `gains=0.5,0.3`: try these turf gains (Oval3DTurf.turf_gain) instead of the game's; `slots=day`.
var gains: Array = [1.0]
var gains_given := false
var slots: Array = SLOTS


func _initialize() -> void:
	_run.call_deferred()
	create_timer(3000.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://tv_colour"
	calibrate = "calibrate" in args
	for a in args:
		if str(a).begins_with("gains="):
			gains_given = true
			gains = Array(str(a).substr(6).split(",")).map(func(x): return float(x))
		elif str(a).begins_with("slots="):
			slots = Array(str(a).substr(6).split(","))
	var grounds: Array = Array(args.slice(1)).filter(func(a): return a != "calibrate" and not "=" in str(a))
	if grounds.is_empty():
		grounds = ["MCG", "Optus Stadium", "Marvel Stadium"]
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	root.size = SIZE
	DisplayServer.window_set_size(SIZE)
	var gdb = root.get_node("GameDB")
	var Squad_ = load("res://scripts/sim/Squad.gd")
	var res: Dictionary = load("res://scripts/sim/MatchSim.gd").new(Squad_.new("SYD", gdb.club_list("SYD"), true, "SYD"),
			Squad_.new("WCE", gdb.club_list("WCE"), false, "WCE"), 31).run()
	for g in grounds:
		var d = load("res://scripts/ui/match/MatchDirector.gd").new()
		d.setup(res, res["events"])
		var oval = load("res://scripts/ui/match/Oval3D.gd").new()
		oval.ground = str(g)
		root.add_child(oval)
		oval.build(d, "SYD", "WCE")
		var tv = load("res://scripts/ui/match/Oval3DBroadcast.gd").new(oval)
		var slug := GroundModels.slug_for(str(g))
		if slug == "":
			slug = str(g).to_snake_case()
		oval.turf.apply("", "day")
		var played := 0.0
		while played < AT:
			d.advance(DT)
			oval.sync(DT)
			tv.frame(DT)
			played += DT
			await process_frame
		var card := _grey_card(oval)
		for slot in slots:
			oval.turf.apply("", slot)
			var variants: Array = [[false, 1.0]]
			for tg in gains:
				variants.append([true, tg])
			for vt in variants:
				var on: bool = vt[0]
				var film: ShaderMaterial = oval.turf.film
				if gains_given:
					oval.turf.turf_gain = float(vt[1])
				oval.turf.broadcast = 1.0 if on else 0.0
				oval.sync(0.0)
				tv.frame(0.0)
				card.global_position = _card_spot(oval)
				card.visible = true
				var gain := Vector3.ONE
				# Balance on the card: each pass scales the gains by how far it is from grey.
				for k in (CALIBRATE if on and calibrate else 1):
					film.set_shader_parameter("balance", gain if calibrate else film.get_shader_parameter("balance"))
					for i in 30:
						await process_frame
					var shot: Image = root.get_viewport().get_texture().get_image()
					var cp0: Vector2 = oval.camera.unproject_position(card.global_position)
					var lin := _lin(_mean(shot, Vector2i(cp0), 4))
					var m := (lin.x + lin.y + lin.z) / 3.0
					if on and calibrate:
						gain *= Vector3(pow(m / maxf(lin.x, 1e-4), 0.7), pow(m / maxf(lin.y, 1e-4), 0.7), pow(m / maxf(lin.z, 1e-4), 0.7))
						gain /= gain.y
				if on and calibrate:
					print("BALANCE %s %s (%.3f, %.3f, %.3f)" % [slug, slot, gain.x, gain.y, gain.z])
				# The record picture without the card in it.
				var cpos: Vector3 = card.global_position
				card.visible = false
				for i in 20:
					await process_frame
				var img: Image = root.get_viewport().get_texture().get_image()
				card.visible = true
				for i in 20:
					await process_frame
				var cimg: Image = root.get_viewport().get_texture().get_image()
				var name := "%s_%s_%s" % [slug, slot, ("on" + ("_%s" % vt[1] if gains_given else "")) if on else "off"]
				img.save_png(out.path_join(name + ".png"))
				var cp: Vector2 = oval.camera.unproject_position(cpos)
				print("COLOUR %s grass %s card %s" % [name, _grass(img), _rgb(_mean(cimg, Vector2i(cp), 4))])
				# Close on the ball, for skin and guernseys.
				card.visible = false
				var cam: Camera3D = oval.camera
				var keep := [cam.global_transform, cam.fov, cam.near]
				var near_man := _closest_player(oval, cam)
				cam.near = 0.05
				cam.fov = 28.0
				cam.global_position = near_man + Vector3(-3.0, 1.6, 4.2)
				cam.look_at(near_man + Vector3(0, 1.3, 0), Vector3.UP)
				for i in 20:
					await process_frame
				root.get_viewport().get_texture().get_image().save_png(out.path_join(name + "_close.png"))
				cam.global_transform = keep[0]
				cam.fov = keep[1]
				cam.near = keep[2]
				card.visible = true
		oval.queue_free()
		await process_frame
	quit(0)


## A photographer's 18% grey card, 3 m square, lying on the turf in open light (no shadow falls
## on it), so the picture's white balance can be read off it as the grass is lit.
func _grey_card(oval: Node3D) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(3.0, 3.0)
	q.orientation = PlaneMesh.FACE_Y
	m.mesh = q
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.18, 0.18, 0.18).linear_to_srgb()
	mat.roughness = 1.0
	mat.disable_receive_shadows = true
	m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	m.material_override = mat
	oval.add_child(m)
	return m


## A spot on the turf a little in front of where the camera aims, the card turned to face it.
func _card_spot(oval: Node3D) -> Vector3:
	var cam: Camera3D = oval.camera
	var f := -cam.global_transform.basis.z
	var t := -cam.global_position.y / minf(f.y, -0.05)
	var at := cam.global_position + f * t * 0.92
	at.y = 0.03
	return at


## The player nearest the middle of the picture, where he stands.
func _closest_player(oval: Node3D, cam: Camera3D) -> Vector3:
	var best := Vector3.ZERO
	var bd := INF
	var mid := Vector2(root.size) * 0.5
	for p in oval.players:
		var n: Node3D = p["node"]
		if not cam.is_position_in_frustum(n.global_position):
			continue
		var dd := cam.unproject_position(n.global_position).distance_to(mid)
		if dd < bd:
			bd = dd
			best = n.global_position
	return best


func _lin(v: Vector3) -> Vector3:
	var c := Color(v.x, v.y, v.z).srgb_to_linear()
	return Vector3(c.r, c.g, c.b)


func _mean(img: Image, at: Vector2i, r: int) -> Vector3:
	var s := Vector3.ZERO
	var n := 0
	for y in range(at.y - r, at.y + r + 1):
		for x in range(at.x - r, at.x + r + 1):
			if x < 0 or y < 0 or x >= img.get_width() or y >= img.get_height():
				continue
			var c := img.get_pixel(x, y)
			s += Vector3(c.r, c.g, c.b)
			n += 1
	return s / maxf(1.0, n)


## Open grass: the lower 40% of the picture, pixels that are green (players, the ball and white
## markings left out).
func _grass(img: Image) -> String:
	var s := Vector3.ZERO
	var n := 0
	for y in range(int(img.get_height() * 0.6), img.get_height() - 8, 3):
		for x in range(8, img.get_width() - 8, 3):
			var c := img.get_pixel(x, y)
			if c.g > c.r and c.g > c.b and c.g - c.b > 0.04 and c.get_luminance() < 0.8:
				s += Vector3(c.r, c.g, c.b)
				n += 1
	return _rgb(s / maxf(1.0, n))


func _rgb(v: Vector3) -> String:
	return "(%d, %d, %d)" % [roundi(v.x * 255.0), roundi(v.y * 255.0), roundi(v.z * 255.0)]
