extends SceneTree
## PROTOTYPE capture: the boots on the 3D footballer (row 197, director 2026-11-15: "Real boots").
##   godot --path . --script tools/visual/capture_oval3d_boots.gd -- OUTDIR
## Three footballers standing (idle) and two mid-stride (jog at a quarter and three quarters of
## the cycle), on the 3D ground. Saves the feet from the front, the side and behind at close
## range (feet_*.png), and the line of them from the match camera's height (game.png).

const CLUBS := ["FRE", "MEL", "WBD", "STK", "FRE"]
const NUMBERS := [23, 5, 7, 12, 30]
const GAP := 1.4


func _initialize() -> void:
	_run.call_deferred()
	create_timer(240.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_boots"
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
		var ap: AnimationPlayer = p["anim"]
		if i >= 3:
			ap.play("jog")
			ap.seek(ap.current_animation_length * (0.25 if i == 3 else 0.75), true)
		ap.advance(1e-4)
		var nd: Node3D = p["node"]
		nd.position = Vector3((i - (CLUBS.size() - 1) * 0.5) * GAP, 0.0, 0.0)
		figs.append(nd)
	var cam := Camera3D.new()
	cam.fov = 30.0
	root.add_child(cam)
	cam.make_current()
	var fwd := _facing(figs[0])
	var side := fwd.cross(Vector3.UP).normalized()
	print("FACING ", fwd)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	_size(Vector2i(1600, 900))
	# The match camera's view: about 30 m off, 14 m up, looking down on the line.
	var mid := Vector3(0.0, 0.9, 0.0)
	cam.fov = 12.0
	cam.position = mid + fwd * 26.0 + side * 8.0 + Vector3(0.0, 14.0, 0.0)
	cam.look_at(mid)
	await _settle()
	await _save(out, "game")
	cam.fov = 30.0
	_size(Vector2i(900, 700))
	for i in range(CLUBS.size()):
		var at: Vector3 = figs[i].position + Vector3(0.0, 0.18, 0.0)
		for view in [["front", fwd], ["side", side], ["back", -fwd]]:
			cam.position = at + (view[1] as Vector3) * 1.3 + Vector3(0.0, 0.25, 0.0)
			cam.look_at(at)
			await _settle()
			await _save(out, "feet_%d_%s" % [i, view[0]])
	print("DONE ", out)
	quit()


## The direction the rest pose's chest faces, from the mesh: the guernsey's front (front 1,
## stored in UV2.y as 1 - front by glTF) is on this side of the body.
func _facing(fig: Node3D) -> Vector3:
	var mi: MeshInstance3D = fig.find_children("*", "MeshInstance3D", true, false)[0]
	var front := Vector3.ZERO
	var back := Vector3.ZERO
	var nf := 0
	var nb := 0
	for s in range(mi.mesh.get_surface_count()):
		var arr: Array = mi.mesh.surface_get_arrays(s)
		var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var uv2: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV2]
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
