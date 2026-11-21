extends SceneTree
## Every Club Forge hair style on the 3D footballer (Oval3D.look), for the art check.
##   godot --path . --script tools/visual/capture_oval3d_hair.gd -- OUTDIR [HAIR_GLB] [--mh] [--no-a2c]
## HAIR_GLB: a candidate hair set (res://...) in place of Oval3D.HAIR_GLB; only its styles show.
## --mh: on the MetaHuman footballer (player_mh.glb), the styles refitted to its head (Oval3D._refit_hair).
## --no-a2c: hair cards blended instead of alpha to coverage (lavapipe, the cloud renderer, drops every
##   card with it), so their soft ends still show.
## --only=a,b: just those styles.
## One footballer per style (Appearance.HAIR_STYLES) in a line on the 3D ground, standing
## (idle), in a plain kit, each a different skin and hair colour: line.png from the broadcast
## height, then head_<style>.png: front, side and back of his head at 3x, one image each.

const GAP := 1.4
## [skin, hair] per style in turn, so every colour pairing shows somewhere.
const LOOKS := [[1, 2], [4, 0], [0, 4], [2, 1], [3, 0], [1, 5], [5, 0], [0, 3]]


func _initialize() -> void:
	_run.call_deferred()
	create_timer(1500.0).timeout.connect(func(): print("TIMEOUT"); quit(1))


func _run() -> void:
	await process_frame
	var args := Array(OS.get_cmdline_user_args())
	var mh := args.has("--mh")
	var no_a2c := args.has("--no-a2c")
	args.erase("--mh")
	args.erase("--no-a2c")
	var only := []
	for a in args.duplicate():
		if str(a).begins_with("--only="):
			only = str(a).trim_prefix("--only=").split(",")
			args.erase(a)
	var out := str(args[0]) if args.size() > 0 else "user://oval3d_hair"
	DirAccess.make_dir_recursive_absolute(out)
	OS.low_processor_usage_mode = false
	var gdb = root.get_node("GameDB")
	var O3 = load("res://scripts/ui/match/Oval3D.gd")
	if mh:
		O3.player_glb = "res://assets/oval3d/player_mh.glb"
		O3.loops_glb = O3.player_glb
	var oval = O3.new()
	root.add_child(oval)
	oval._environment()
	oval._ground()
	# The match's own light (rules 2.80-2.81: a fine day), as Oval3D.build sets it.
	if oval.turf != null:
		oval.turf.apply("perfect", "day")
	var scene: PackedScene = load(O3.player_glb)
	var styles: Array = Appearance.HAIR_STYLES
	if args.size() > 1:
		oval.hair_glb = str(args[1])
		styles = oval.hair_shells().keys()
	if not only.is_empty():
		styles = styles.filter(func(st): return only.has(st))
		styles.sort()
	var figs := []
	for i in range(styles.size()):
		var p: Dictionary = oval._player(scene, oval._kit(gdb.club_guernsey("FRE")), gdb.club_colours("FRE"))
		var lk: Array = LOOKS[i % LOOKS.size()]
		oval.look(p, {"skin": lk[0], "hair": lk[1], "hair_style": styles[i]}, true)
		if no_a2c and p.get("hair_node") is Node:
			for hm in (p["hair_node"] as Node).find_children("*", "MeshInstance3D", true, false):
				var hmat := ((hm as MeshInstance3D).material_override as StandardMaterial3D).duplicate()
				hmat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
				# Soft strand ends, as alpha to coverage draws them on a phone: blended over a
				# depth pre-pass, so the cards still sort.
				if hmat.albedo_texture != null:
					hmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
				(hm as MeshInstance3D).material_override = hmat
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
