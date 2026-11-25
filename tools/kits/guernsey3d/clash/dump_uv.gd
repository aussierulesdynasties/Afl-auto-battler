extends SceneTree
## Writes each club cut's guernsey triangles in its picture coordinates (the atlas cell square the shader
## reads, front and back) so a clash photo can be fitted to the outline the home photo gave the cut.
##   godot --headless --path . --script tools/kits/guernsey3d/clash/dump_uv.gd -- OUT_DIR CODE...
## OUT_DIR/uv_CODE.json (and unwrap_CODE.json for a club with a flat pattern): {"front": [[x0,y0,x1,y1,x2,y2], ...], "back": [...]} in 0..1 of the square.

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	var O3 = load("res://scripts/ui/match/Oval3D.gd")
	var args := OS.get_cmdline_user_args()
	var out_dir := str(args[0])
	var base: Node = (load("res://assets/oval3d/player_mh.glb") as PackedScene).instantiate()
	var mi := _biggest(base)
	for k in range(1, args.size()):
		var code := str(args[k])
		var m := O3.club_body(mi.mesh, code) as ArrayMesh
		var s := -1
		for i in range(m.get_surface_count()):
			if O3._surface_name(m, i) == "ARD_guernsey":
				s = i
		var a := m.surface_get_arrays(s)
		var uv: PackedVector2Array = a[Mesh.ARRAY_TEX_UV]
		var uv2: PackedVector2Array = a[Mesh.ARRAY_TEX_UV2]
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		var res := {"front": [], "back": []}
		for t in range(0, idx.size(), 3):
			var zs := [1.0 - uv2[idx[t]].y, 1.0 - uv2[idx[t + 1]].y, 1.0 - uv2[idx[t + 2]].y]
			var side := ""
			if zs.min() > 0.98:
				side = "front"
			elif zs.max() < 0.02:
				side = "back"
			else:
				continue
			var tri := []
			for j in range(3):
				var g := uv[idx[t + j]]
				var gx := g.x if side == "front" else 1.0 - g.x
				tri.append_array([gx, g.y])
			res[side].append(tri)
		var f := FileAccess.open("%s/uv_%s.json" % [out_dir, code], FileAccess.WRITE)
		f.store_string(JSON.stringify(res))
		# A club cut with a flat pattern (cut_res.gd's <name>_unwrap, CUSTOM3 = 1 + place): bake_unwrap.py's
		# unwrap_CODE.json, so a clash picture can be baked onto the same pattern (g: x, y, z, uv, pattern place).
		var c3 = a[Mesh.ARRAY_CUSTOM3]
		if c3 is PackedFloat32Array and (c3 as PackedFloat32Array).size() == uv.size() * 2:
			var pv: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
			var g := []
			for i in range(pv.size()):
				g.append([pv[i].x, pv[i].y, pv[i].z, uv[i].x, uv[i].y, c3[i * 2] - 1.0, c3[i * 2 + 1] - 1.0])
			var fu := FileAccess.open("%s/unwrap_%s.json" % [out_dir, code], FileAccess.WRITE)
			fu.store_string(JSON.stringify({"g": g, "t": Array(idx)}))
			print("UNWRAP ", code, " points ", pv.size())
		print("UV ", code, " front ", res.front.size(), " back ", res.back.size())
	quit()

func _biggest(n: Node) -> MeshInstance3D:
	var best: MeshInstance3D = null
	for c in n.find_children("*", "MeshInstance3D", true, false):
		if best == null or (c as MeshInstance3D).mesh.get_surface_count() > best.mesh.get_surface_count():
			best = c
	return best
