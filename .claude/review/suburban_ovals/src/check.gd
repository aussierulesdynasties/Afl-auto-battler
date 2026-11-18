extends SceneTree
func _count(n: Node) -> Array:
	var m := 0; var t := 0
	if n is MeshInstance3D and n.mesh:
		m += 1
		for s in n.mesh.get_surface_count():
			var a = n.mesh.surface_get_arrays(s)
			t += (a[Mesh.ARRAY_INDEX].size() if a[Mesh.ARRAY_INDEX] else a[Mesh.ARRAY_VERTEX].size()) / 3
	for c in n.get_children():
		var r := _count(c); m += r[0]; t += r[1]
	return [m, t]
func _init():
	for f in DirAccess.get_files_at("res://ovals"):
		if f.ends_with(".tscn"):
			var ps: PackedScene = load("res://ovals/" + f)
			var n := ps.instantiate() if ps else null
			var r := _count(n) if n else [0, 0]
			print("LOADED ", f, " meshes ", r[0], " tris ", r[1])
			if n: n.free()
	quit()
