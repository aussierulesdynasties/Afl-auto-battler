class_name SupporterMerch
extends RefCounted
## Puts a club's colours on a close-up supporter's scarf and beanie at run time (any club, Forge clubs too).
## The supporter GLB's knitwear materials are named SUP_scarf and SUP_beanie; their textures carry the knit and
## the stripe layout, never a colour (see assets/oval3d/supporters/merch_knit.gdshader).

const SHADER := preload("res://assets/oval3d/supporters/merch_knit.gdshader")


## scarf: 1-4 colours, the stripes repeat them in order from each end. beanie: dark band, light band.
static func dress(root: Node, scarf: Array, beanie: Array) -> int:
	var done := 0
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for si in mesh.get_surface_count():
			var mat := mesh.surface_get_material(si)
			var nm := mat.resource_name if mat != null else ""
			if not (nm.begins_with("SUP_scarf") or nm.begins_with("SUP_beanie")):
				continue
			var is_beanie := nm.begins_with("SUP_beanie")
			var sm := ShaderMaterial.new()
			sm.shader = SHADER
			var tex: Texture2D = (mat as BaseMaterial3D).albedo_texture if mat is BaseMaterial3D else null
			sm.set_shader_parameter("knit", tex)
			sm.set_shader_parameter("stripe_id", tex)
			if mat is BaseMaterial3D and (mat as BaseMaterial3D).normal_texture != null:
				sm.set_shader_parameter("knit_normal", (mat as BaseMaterial3D).normal_texture)
				sm.set_shader_parameter("use_normal", true)
			sm.set_shader_parameter("beanie", is_beanie)
			var cols: Array = beanie if is_beanie else scarf
			for i in 4:
				sm.set_shader_parameter("colour_%d" % i, Color(cols[min(i, cols.size() - 1)]))
			sm.set_shader_parameter("colour_count", clampi(cols.size(), 1, 4))
			(mi as MeshInstance3D).set_surface_override_material(si, sm)
			done += 1
	return done
