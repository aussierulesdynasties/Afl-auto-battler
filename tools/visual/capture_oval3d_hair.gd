extends SceneTree
## Every Club Forge hair style on the 3D footballer (Oval3D.look), for the art check.
##   godot --path . --script tools/visual/capture_oval3d_hair.gd -- OUTDIR
## One footballer per style (Appearance.HAIR_STYLES) in a line on the 3D ground, standing
## (idle), in a plain kit, each a different skin and hair colour: line.png from the broadcast
## height, then head_<style>.png: front, side and back of his head at 3x, one image each.

const GAP := 1.4
## [skin, hair] per style in turn, so every colour pairing shows somewhere.
const LOOKS := [[1, 2], [4, 0], [0, 4], [2, 1], [3, 0], [1, 5], [5, 0], [0, 3]]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(300.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := OS.get_cmdline_user_args()
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_hair"
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var oval = load("res://scripts/ui/match/Oval3D.gd").new()
	root.add_child(oval)
	oval._environment()
	oval._ground()
	var scene: PackedScene = load(oval.PLAYER_GLB)
	var styles: Array = Appearance.HAIR_STYLES
	var figs := []
	for i in range(styles.size()):
		var p: Dictionary = oval._player(scene, oval._kit(gdb.club_guernsey("FRE")), gdb.club_colours("FRE"))
		var lk: Array = LOOKS[i % LOOKS.size()]
		oval.look(p, {"skin": lk[0], "hair": lk[1], "hair_style": styles[i]})
		(p["anim"] as AnimationPlayer).advance(1e-4)
		var nd: Node3D = p["node"]
		nd.position = Vector3((i - (styles.size() - 1) * 0.5) * GAP, 0.0, 0.0)
		figs.append(nd)
		print("STYLE ", styles[i], " shell ", p.has("hair_node"))
	var cam := Camera3D.new()
	cam.fov = 30.0
	root.add_child(cam)
	cam.make_current()
	var fwd := _facing(figs[0])
	var right := fwd.cross(Vector3.UP).normalized()
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	_size(Vector2i(2400, 700))
	var width := styles.size() * GAP
	var dist := width * 0.5 / tan(deg_to_rad(cam.fov * 0.5)) / (2400.0 / 700.0) * 1.05
	cam.position = Vector3(0.0, 1.1, 0.0) + fwd * dist
	cam.look_at(Vector3(0.0, 1.0, 0.0))
	await _settle()
	await _save(out, "line")
	_size(Vector2i(1200, 420))
	for i in range(styles.size()):
		var at: Vector3 = figs[i].position + Vector3(0.0, 1.72, 0.0)
		var shots := []
		for d in [fwd, right, -fwd]:
			cam.position = at + d * 1.1 + Vector3(0.0, 0.08, 0.0)
			cam.look_at(at)
			await _settle()
			await RenderingServer.frame_post_draw
			shots.append(root.get_viewport().get_texture().get_image())
		var w: int = shots[0].get_width() / 3
		var img := Image.create(w * 3, shots[0].get_height(), false, Image.FORMAT_RGBA8)
		for k in range(3):
			var s: Image = shots[k]
			s.convert(Image.FORMAT_RGBA8)
			img.blit_rect(s, Rect2i(w, 0, w, s.get_height()), Vector2i(w * k, 0))
		img.save_png(out.path_join("head_%02d_%s.png" % [i, styles[i]]))
	print("DONE ", out)
	quit()


## The direction the rest pose's chest faces (capture_oval3d_kits.gd).
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
