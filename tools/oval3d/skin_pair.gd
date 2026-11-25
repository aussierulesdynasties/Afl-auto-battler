extends SceneTree
## The two men's skinned body meshes, frame by frame, for the mesh-level overlap check
## (check_mesh_pair.py): the real skin and kit surface, not the rough capsules of check_pair.gd.
##   godot --headless --path . --script tools/oval3d/skin_pair.gd -- A.res B.res OUT_DIR [HZ] [FROM TO]
## Writes OUT_DIR/faces.i32 (triangles, shared by both men: one body mesh), OUT_DIR/a_<n>.f32 and
## b_<n>.f32 (each man's skinned vertex positions, metres, little-endian float32 xyz) for frames
## FROM..TO at HZ (default 25: every frame of a 25 Hz clip). Skinned on the CPU exactly as the GPU
## does it (each vertex: the weighted sum of bone global pose x bind pose), each clip played inside
## ClipLimits as the match plays it.

const GLB := "res://assets/oval3d/player_mh.glb"


func _initialize() -> void:
	_run.call_deferred()


func _man(res: String) -> Dictionary:
	var scene: Node3D = (load(GLB) as PackedScene).instantiate()
	root.add_child(scene)
	var ap: AnimationPlayer = scene.find_children("*", "AnimationPlayer", true, false)[0]
	var sk: Skeleton3D = scene.find_children("*", "Skeleton3D", true, false)[0]
	var lib := AnimationLibrary.new()
	lib.add_animation("clip", load(res))
	ap.add_animation_library("pair", lib)
	ClipLimits.apply(ap, sk)
	ap.play("pair/clip")
	ap.pause()
	var mi: MeshInstance3D = scene.find_children("*", "MeshInstance3D", true, false)[0]
	return {"ap": ap, "sk": sk, "mi": mi}


func _run() -> void:
	await process_frame
	var a := OS.get_cmdline_user_args()
	var out := str(a[2])
	var hz := float(a[3]) if a.size() > 3 else 25.0
	DirAccess.make_dir_recursive_absolute(out)
	var men := [_man(str(a[0])), _man(str(a[1]))]
	var mi: MeshInstance3D = men[0]["mi"]
	var mesh := mi.mesh
	var skin := mi.skin
	# The mesh once: vertices, bone indices and weights per surface, joined; triangles offset.
	var verts := PackedVector3Array()
	var bones := PackedInt32Array()
	var weights := PackedFloat32Array()
	var faces := PackedInt32Array()
	var per := 4
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var bi: PackedInt32Array = arr[Mesh.ARRAY_BONES]
		var bw: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
		per = bi.size() / maxi(1, v.size())
		var base := verts.size()
		verts.append_array(v)
		bones.append_array(bi)
		weights.append_array(bw)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		for k in idx.size():
			faces.append(idx[k] + base)
	var f := FileAccess.open(out.path_join("faces.i32"), FileAccess.WRITE)
	f.store_buffer(faces.to_byte_array())
	f.close()
	var nb := skin.get_bind_count()
	var length: float = (men[0]["ap"] as AnimationPlayer).current_animation_length
	var n0 := int(a[4]) if a.size() > 5 else 0
	var n1 := int(a[5]) if a.size() > 5 else int(floor(length * hz + 1e-4))
	for n in range(n0, n1 + 1):
		for m in 2:
			var man: Dictionary = men[m]
			var sk: Skeleton3D = man["sk"]
			(man["ap"] as AnimationPlayer).seek(n / hz, true)
			var mats := []
			for i in nb:
				var b := skin.get_bind_bone(i)
				if b < 0:
					b = sk.find_bone(skin.get_bind_name(i))
				mats.append(sk.global_transform * sk.get_bone_global_pose(b) * skin.get_bind_pose(i))
			var outv := PackedFloat32Array()
			outv.resize(verts.size() * 3)
			for vi in verts.size():
				var p := Vector3.ZERO
				var w := 0.0
				for j in per:
					var ww := weights[vi * per + j]
					if ww <= 0.0:
						continue
					p += (mats[bones[vi * per + j]] as Transform3D) * verts[vi] * ww
					w += ww
				if w > 0.0:
					p /= w
				outv[vi * 3] = p.x
				outv[vi * 3 + 1] = p.y
				outv[vi * 3 + 2] = p.z
			var g := FileAccess.open(out.path_join("%s_%d.f32" % ["a" if m == 0 else "b", n]), FileAccess.WRITE)
			g.store_buffer(outv.to_byte_array())
			g.close()
	print("SKINNED %d..%d (%d verts, %d triangles)" % [n0, n1, verts.size(), faces.size() / 3])
	quit()
