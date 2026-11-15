extends SceneTree
## PROTOTYPE capture: every club design on the 3D footballer (row 197), for the art check.
##   godot --path . --script tools/visual/capture_oval3d_kits.gd -- OUTDIR
## One footballer per design in a line on the 3D ground, standing (idle), each in his club's
## home guernsey (GameDB.club_guernsey) with a number: front.png from in front, back.png from
## behind, and close_<code>.png front and back of each at 2x for the seams.

const CLUBS := ["ADE", "BRL", "ESS", "FRE", "GEE", "GCS", "GWS", "HAW", "PAD", "RIC", "STK", "WCE", "WBD", "TAS"]
const NUMBERS := [9, 4, 17, 23, 5, 31, 12, 1, 44, 8, 26, 30, 7, 18]
const GAP := 1.6


func _initialize() -> void:
	_run.call_deferred()
	create_timer(240.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_kits"
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false   # else nothing redraws a still scene and the save waits forever
	var gdb = root.get_node("GameDB")
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval._environment()
	oval._ground()
	var scene: PackedScene = load(oval.PLAYER_GLB)
	var figs := []
	for i in range(CLUBS.size()):
		var code: String = CLUBS[i]
		var p: Dictionary = oval._player(scene, oval._kit(gdb.club_guernsey(code)), gdb.club_colours(code))
		oval._number(p, NUMBERS[i])
		(p["anim"] as AnimationPlayer).advance(1e-4)
		var nd: Node3D = p["node"]
		nd.position = Vector3((i - (CLUBS.size() - 1) * 0.5) * GAP, 0.0, 0.0)
		figs.append(nd)
	var cam := Camera3D.new()
	cam.fov = 30.0
	root.add_child(cam)
	cam.make_current()
	# Which way the body faces at rest: the camera goes on the side the chest points to.
	var fwd := _facing(figs[0])
	print("FACING ", fwd)
	var width := CLUBS.size() * GAP
	var dist := width * 0.5 / tan(deg_to_rad(cam.fov * 0.5)) / (16.0 / 9.0) * 1.08
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	_size(Vector2i(2400, 600))
	for side in [["front", 1.0], ["back", -1.0]]:
		cam.position = Vector3(0.0, 1.1, 0.0) + fwd * dist * float(side[1]) * 0.42
		cam.look_at(Vector3(0.0, 1.0, 0.0))
		cam.fov = 30.0
		await _settle()
		await _save(out, str(side[0]))
		print("SAVED ", side[0])
	_size(Vector2i(900, 1000))
	for i in range(CLUBS.size()):
		for side in [["front", 1.0], ["back", -1.0]]:
			var at: Vector3 = figs[i].position + Vector3(0.0, 1.25, 0.0)
			cam.position = at + fwd * 2.6 * float(side[1]) + Vector3(0.0, 0.15, 0.0)
			cam.look_at(at)
			await _settle()
			await _save(out, "close_%s_%s" % [CLUBS[i], side[0]])
	# The legs: shorts, socks and their band, boots.
	for i in [CLUBS.find("GEE"), CLUBS.find("RIC"), CLUBS.find("WBD")]:
		var at: Vector3 = figs[i].position + Vector3(0.0, 0.45, 0.0)
		cam.position = at + fwd * 2.2 + Vector3(0.0, 0.1, 0.0)
		cam.look_at(at)
		await _settle()
		await _save(out, "legs_%s" % CLUBS[i])
	print("DONE ", out)
	quit()


## The direction the rest pose's chest faces, from the mesh: the guernsey's front (front 1,
## stored in UV2.y as 1 - front by glTF) is on this side of the body.
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


func _size(sz: Vector2i) -> void:
	root.size = sz
	DisplayServer.window_set_size(sz)


func _settle() -> void:
	for k in range(3):
		await process_frame


func _save(out: String, name: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_viewport().get_texture().get_image().save_png(out.path_join(name + ".png"))
