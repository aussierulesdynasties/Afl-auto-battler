extends SceneTree
# dump.gd -- out.bin in1.glb [in2.glb...]: every triangle of the models, world space, float32 xyz x3.
func _init():
	var a := OS.get_cmdline_user_args()
	var out := PackedVector3Array()
	for path in a.slice(1):
		var doc := GLTFDocument.new(); var st := GLTFState.new()
		if doc.append_from_file(path, st) != OK: print("FAIL ", path); continue
		var root := doc.generate_scene(st)
		for mi in root.find_children("*", "MeshInstance3D", true, false):
			var t := _xf(mi)
			var f: PackedVector3Array = mi.mesh.get_faces()
			for i in f.size(): f[i] = t * f[i]
			out.append_array(f)
		root.free()
	var fa := FileAccess.open(a[0], FileAccess.WRITE)
	fa.store_buffer(out.to_byte_array())
	print("wrote ", a[0], " tris=", out.size() / 3)
	quit()
func _xf(n: Node) -> Transform3D:
	var t := Transform3D.IDENTITY
	var c := n
	while c is Node3D:
		t = (c as Node3D).transform * t
		c = c.get_parent()
	return t
