class_name Oval3DCrew
extends RefCounted
## The match crew's clothes (row 202): what the boundary and goal umpires, trainers and runners
## wear over the shared body, as real AFL broadcasts show them in 2026.
##
## The clothes are modelled, not painted (tools/oval3d/crew/build_crew.py builds them from the
## body they fit, one file per body): the umpires' short-sleeved shirt, the goal umpire's long
## trousers, belt, buckle and cap, the trainer's AFL vest. Each piece rides the wearer's own
## skeleton, bound by bone name, and takes the body's build (its blend shapes), so it moves and
## sizes with him. What the clothes cover of the body is left out of his body mesh (covered), so
## no skin or shorts show through a sleeve or a trouser leg as he runs.
##
## The kit shader colours the clothes by their region (Color: r guernsey, g shorts): the shirt
## and vest wear the kit's guernsey colour and number, the trousers its shorts colour.

const AVERAGE_GLB := "res://assets/oval3d/crew_average.glb"
const MH_GLB := "res://assets/oval3d/crew_mh.glb"

## What each crew role wears over the body.
const OUTFITS := {
	"field": ["crew_shirt"],
	"boundary": ["crew_shirt"],
	"goal": ["crew_shirt", "crew_trousers", "crew_belt", "crew_buckle", "crew_cap"],
	"trainer": ["crew_shirt", "crew_vest"],
	"runner": ["crew_shirt"],
}

## The kit shader draws these pieces (their region colours); the others have their own material.
const KIT_PIECES := ["crew_shirt", "crew_trousers", "crew_vest", "crew_cap"]

## The AFL-supplied trainer's vest (Regulation 12.17: "an AFL supplied vest indicating their
## respective function"), purple, its number on the back. Colour from 2025-26 match photos.
const TRAINER_VEST := Color8(187, 117, 216)
## The runner's top (Regulation 12.13's runner), fluoro pink.
const RUNNER_TOP := Color(0.96, 0.36, 0.62)
## The goal umpire's belt: black leather; its buckle: brushed steel.
const BELT := Color(0.03, 0.03, 0.03)
const BUCKLE := Color(0.62, 0.62, 0.6)

## Real 2026 AFL field umpires' numbers (the round 1 appointments): a field umpire's shirt
## carries one on its back. Boundary and goal umpires wear none.
const FIELD_NUMBERS := [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 24,
		25, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41]

## The bones of the legs and hips: skin there under the trousers is covered.
const LEG_BONES := ["pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r"]

static var _pieces := {}
static var _covered := {}


## The crew file made for the body in player_glb.
static func glb_for(player_glb: String) -> String:
	return MH_GLB if player_glb.get_file().begins_with("player_mh") else AVERAGE_GLB


## Each piece of the crew file, read once: {name: {"mesh", "skin", "at"}}. A worn piece's skin
## binds by bone name (so it rides any skeleton with the same bones) and "at" is its place
## relative to its skeleton; a hand-held piece (a flag, a bottle) has no skin.
static func pieces(glb: String) -> Dictionary:
	if _pieces.has(glb):
		return _pieces[glb]
	var out := {}
	_pieces[glb] = out
	if not ResourceLoader.exists(glb):
		return out
	var scene := load(glb) as PackedScene
	if scene == null:
		return out
	var root: Node3D = scene.instantiate()
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		var entry := {"mesh": m.mesh}
		var skel := m.get_node_or_null(m.skeleton) as Skeleton3D
		if m.skin != null and skel != null:
			var sk := Skin.new()
			for b in range(m.skin.get_bind_count()):
				var nm := str(m.skin.get_bind_name(b))
				var bone := m.skin.get_bind_bone(b)
				if nm == "" and bone >= 0:
					nm = skel.get_bone_name(bone)
				sk.add_named_bind(nm, m.skin.get_bind_pose(b))
			entry["skin"] = sk
			entry["at"] = _rel(skel, m)
		else:
			entry["at"] = _rel(root, m)
		out[str(m.name)] = entry
	root.free()
	return out


## n's transform relative to the ancestor `to` (not in a tree: parent by parent).
static func _rel(to: Node, n: Node3D) -> Transform3D:
	var t := Transform3D.IDENTITY
	var at: Node = n
	while at != null and at != to:
		if at is Node3D:
			t = (at as Node3D).transform * t
		at = at.get_parent()
	return t


## Dresses figure p (Oval3D._player's dictionary) for `role`: the pieces OUTFITS names, worn on
## his skeleton, and his body mesh without what they cover. kit: his kit material (shirt, vest,
## trousers, cap); vest: the trainer vest's own kit material, when he wears one. Returns the
## pieces added, by name.
static func dress(p: Dictionary, role: String, player_glb: String, kit: Material, vest: Material = null) -> Dictionary:
	var wear: Array = OUTFITS.get(role, [])
	var all := pieces(glb_for(player_glb))
	var skel: Skeleton3D = p["skel"]
	var body: MeshInstance3D = null
	for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if m.has_meta("kit") and (body == null or m.mesh.get_surface_count() > body.mesh.get_surface_count()):
			body = m
	var out := {}
	for name in wear:
		if not all.has(name) or not (all[name] as Dictionary).has("skin"):
			continue
		var e: Dictionary = all[name]
		var mi := MeshInstance3D.new()
		mi.name = name
		mi.mesh = e["mesh"]
		mi.skin = e["skin"]
		skel.add_child(mi)
		mi.transform = e["at"]
		mi.skeleton = mi.get_path_to(skel)
		match name:
			"crew_vest":
				mi.material_override = vest if vest != null else kit
				mi.set_meta("kit", true)
			"crew_belt":
				mi.material_override = _plain(BELT, 0.55, 0.0)
			"crew_buckle":
				mi.material_override = _plain(BUCKLE, 0.35, 0.9)
			_:
				mi.material_override = kit
				mi.set_meta("kit", true)
		if body != null:
			_same_build(body, mi)
		out[name] = mi
	if body != null:
		var hide := []
		# Only what is really worn hides the body (a crew file missing a piece leaves him as he was).
		if out.has("crew_shirt") or out.has("crew_vest"):
			hide.append("top")
		if out.has("crew_trousers"):
			hide.append("legs")
		if not hide.is_empty():
			var over := []
			for s in range(body.get_surface_override_material_count()):
				over.append(body.get_surface_override_material(s))
			var shapes := []
			for k in range(body.get_blend_shape_count()):
				shapes.append(body.get_blend_shape_value(k))
			body.mesh = covered(body, hide)
			for s in range(over.size()):
				body.set_surface_override_material(s, over[s])
			for k in range(shapes.size()):
				body.set_blend_shape_value(k, shapes[k])
	p["crew"] = out
	return out


## The body's build (its blend shape values, by name) on a worn piece.
static func _same_build(body: MeshInstance3D, piece: MeshInstance3D) -> void:
	for k in range(piece.get_blend_shape_count()):
		var b := body.find_blend_shape_by_name(piece.mesh.get_blend_shape_name(k))
		piece.set_blend_shape_value(k, body.get_blend_shape_value(b) if b >= 0 else 0.0)


static func _plain(c: Color, rough: float, metal: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	m.metallic = metal
	return m


## Body mesh of mi without the triangles clothes cover: "top" the guernsey's surface (under the
## shirt or vest); "legs" the shorts' surface and the leg skin and socks between the waistband and
## the boot (under the trousers). The surfaces keep their order (overrides stay on them) and
## their points (blend shapes stay valid): only their triangles go. Once per mesh and cover.
static func covered(mi: MeshInstance3D, hide: Array) -> Mesh:
	var m := mi.mesh
	var key := [m, hide]
	if _covered.has(key):
		return _covered[key]
	var am := m as ArrayMesh
	if am == null:
		return m
	var waist := -INF
	var boot := -INF
	for s in range(am.get_surface_count()):
		var nm := Oval3D._surface_name(am, s)
		if nm == Oval3D.SHORTS_SURFACE or nm.begins_with("ARD_boot"):
			var vs: PackedVector3Array = am.surface_get_arrays(s)[Mesh.ARRAY_VERTEX]
			for v in vs:
				if nm == Oval3D.SHORTS_SURFACE:
					waist = maxf(waist, v.y)
				else:
					boot = maxf(boot, v.y)
	var legs := {}
	if mi.skin != null:
		var skel := mi.get_node_or_null(mi.skeleton) as Skeleton3D
		for b in range(mi.skin.get_bind_count()):
			var nm := str(mi.skin.get_bind_name(b))
			if nm == "" and skel != null and mi.skin.get_bind_bone(b) >= 0:
				nm = skel.get_bone_name(mi.skin.get_bind_bone(b))
			if nm in LEG_BONES:
				legs[b] = true
	var out := ArrayMesh.new()
	out.blend_shape_mode = am.blend_shape_mode
	for b in range(am.get_blend_shape_count()):
		out.add_blend_shape(am.get_blend_shape_name(b))
	for s in range(am.get_surface_count()):
		var nm := Oval3D._surface_name(am, s)
		var a := am.surface_get_arrays(s)
		var shapes := am.surface_get_blend_shape_arrays(s)
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		var drop_all := (nm == Oval3D.GUERNSEY_SURFACE and "top" in hide) \
				or (nm == Oval3D.SHORTS_SURFACE and "legs" in hide)
		var leg_skin := "legs" in hide and (nm == Oval3D.SKIN_SURFACE or nm == "ARD_sock") \
				and a[Mesh.ARRAY_BONES] != null
		var keep := PackedInt32Array()
		if not drop_all:
			if leg_skin:
				var vs: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
				var bones = a[Mesh.ARRAY_BONES]
				var ws = a[Mesh.ARRAY_WEIGHTS]
				var per: int = (bones.size() / vs.size())
				var under := PackedByteArray()
				under.resize(vs.size())
				for i in range(vs.size()):
					var best := 0
					var bw := -1.0
					for c in range(per):
						if float(ws[i * per + c]) > bw:
							bw = float(ws[i * per + c])
							best = int(bones[i * per + c])
					under[i] = 1 if legs.has(best) and vs[i].y > boot + 0.01 and vs[i].y < waist - 0.005 else 0
				for f in range(0, idx.size(), 3):
					if under[idx[f]] == 0 or under[idx[f + 1]] == 0 or under[idx[f + 2]] == 0:
						keep.append(idx[f])
						keep.append(idx[f + 1])
						keep.append(idx[f + 2])
			else:
				keep = idx
		if keep.is_empty():
			# A surface with nothing left keeps one empty triangle, so every surface after it
			# keeps its index (and its material).
			keep = PackedInt32Array([0, 0, 0])
		a[Mesh.ARRAY_INDEX] = keep
		out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a, shapes, {}, Oval3D._custom_format(am, s))
		out.surface_set_material(s, am.surface_get_material(s))
		out.surface_set_name(s, am.surface_get_name(s))
	_covered[key] = out
	return out


## A field umpire's number for umpire k of a match seeded `seed`: four different real numbers.
static func field_number(seed: int, k: int) -> int:
	var pool := FIELD_NUMBERS.duplicate()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	for i in range(pool.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = pool[i]
		pool[i] = pool[j]
		pool[j] = t
	return int(pool[k % pool.size()])
