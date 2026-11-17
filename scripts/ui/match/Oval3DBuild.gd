class_name Oval3DBuild
extends RefCounted
## Each man's build and face on the 3D oval (row 202, 2d): his real height and weight, and a face
## of his own.
##
## The player GLB carries morph targets made in MetaHuman (D:/AflMH, mh_to_glb_morph.py): four
## corner bodies (short 168 cm, tall 211 cm, light and heavy at 188 cm) and fifteen faces. Beside
## it, <glb>_builds.json holds how far each corner moves every joint. A man is drawn as the
## 188 cm average body blended toward the corners his height and weight reach: his joints move
## by the same blend (so boots, eyes and hair, held rigidly by foot and head, go with him) and the
## morphs add the rest of the shape.
##
## Height: 196 cm is (196 - 188) / (211 - 188) = 35% of the way to the tall corner.
## Weight: what sets his girth is his weight against the real average for his height. In the 2026
## lists (630 men with both) that average is 83.5 kg x (height / 188)^1.96, so the short and tall
## corners are built at it (girth x0.948 at 168 cm, x1.057 at 211 cm). Girth goes with the square
## root of weight over that average, since weight is height x girth squared: Sean Darcy, 113 kg at
## 202 cm against 96.2 kg, is girth x1.08, 70% of the way to the heavy corner (x1.12); Mason Cox,
## 105 kg at 211 cm, is the average for his height and stays on the tall corner's build.

const AVG_CM := 188.0
const SHORT_CM := 168.0
const TALL_CM := 211.0
## The 2026 lists' average weight at 188 cm and how it grows with height (630 players with both,
## players_enriched_2026, fitted as weight = AVG_KG x (height / 188)^HEIGHT_POWER).
const AVG_KG := 83.5
const HEIGHT_POWER := 1.96
## How far the light and heavy corners' girths sit from the average (x 0.88, x 1.12).
const GIRTH_SPAN := 0.12
const FACE_PREFIX := "face_"
## Real 2026 heights and weights, for a man with no weight on record (rule 2.97).
const REAL_CSV := "res://data/players_enriched_2026.csv"

static var _data := {}
## Height in whole cm -> the 2026 lists' weights at that height, sorted.
static var _real := {}


## The morph and joint data beside a player GLB (empty when the GLB has none).
static func data_for(glb: String) -> Dictionary:
	if _data.has(glb):
		return _data[glb]
	var path := glb.get_basename() + "_builds.json"
	var d := {}
	if FileAccess.file_exists(path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
		if parsed is Dictionary:
			d = parsed
	_data[glb] = d
	return d


## A man with no weight on record takes a real man's weight (director, rule 2.97): the weight of a
## 2026 player of his height (the nearest height listed, within 3 cm), which one picked by his
## player id so he keeps it. 0 when nobody that height is listed.
static func real_weight(h_cm: float, pid: String) -> float:
	if _real.is_empty():
		var f := FileAccess.open(REAL_CSV, FileAccess.READ)
		if f != null:
			var head := f.get_csv_line()
			var ih := head.find("height_cm")
			var iw := head.find("weight_kg")
			while ih >= 0 and iw >= 0 and not f.eof_reached():
				var row := f.get_csv_line()
				if row.size() > maxi(ih, iw) and float(row[ih]) > 0.0 and float(row[iw]) > 0.0:
					var k := int(round(float(row[ih])))
					if not _real.has(k):
						_real[k] = []
					_real[k].append(float(row[iw]))
		for k in _real:
			_real[k].sort()
	var h := int(round(h_cm))
	for off in [0, -1, 1, -2, 2, -3, 3]:
		var ws: Array = _real.get(h + off, [])
		if not ws.is_empty():
			return float(ws[hash("weight:" + pid) % ws.size()]) if pid != "" else float(ws[ws.size() / 2])
	return 0.0


## The real average weight for a man of h cm (2026 lists).
static func avg_kg(h_cm: float) -> float:
	return AVG_KG * pow(h_cm / AVG_CM, HEIGHT_POWER)


## Corner weights for a man of h cm and w kg: {"short"|"tall": x, "light"|"heavy": y}. No height:
## the average 188 cm. No weight: the average build for his height.
static func body_weights(h_cm: float, w_kg: float) -> Dictionary:
	var h := h_cm if h_cm > 0.0 else AVG_CM
	var out := {}
	if h >= AVG_CM:
		out["tall"] = (h - AVG_CM) / (TALL_CM - AVG_CM)
	else:
		out["short"] = (AVG_CM - h) / (AVG_CM - SHORT_CM)
	var g := sqrt(w_kg / avg_kg(h)) if w_kg > 0.0 else 1.0
	if g >= 1.0:
		out["heavy"] = (g - 1.0) / GIRTH_SPAN
	else:
		out["light"] = (1.0 - g) / GIRTH_SPAN
	return out


## His face: two of the fifteen, blended, picked by his player id, so no two men share one and a
## man keeps his face every match. {"face_X": weight, "face_Y": weight}.
static func face_weights(pid: String, faces: Array) -> Dictionary:
	if faces.size() < 2 or pid == "":
		return {}
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("face:" + pid)
	var a := rng.randi_range(0, faces.size() - 1)
	var b := (a + rng.randi_range(1, faces.size() - 1)) % faces.size()
	# The two always add up to one whole face, so none of the base face shows through.
	var wa := rng.randf_range(0.55, 1.0)
	return {faces[a]: wa, faces[b]: 1.0 - wa}


## Put a man's build and face on figure p (Oval3D._player's dictionary). who: his player record
## (height_cm, weight_kg), or {} for the average body with no face of his own (umpires keep theirs
## by pid below).
static func apply(p: Dictionary, glb: String, who: Dictionary, pid: String) -> void:
	var d := data_for(glb)
	if d.is_empty():
		return
	var morphs: Dictionary = d.get("morphs", {})
	var faces := []
	for n in morphs:
		if str(n).begins_with(FACE_PREFIX):
			faces.append(n)
	faces.sort()
	var h := float(who.get("height_cm", 0.0))
	var w := float(who.get("weight_kg", 0.0))
	if w <= 0.0 and h > 0.0:
		w = real_weight(h, pid)
	var ws := body_weights(h, w)
	ws.merge(face_weights(pid, faces))
	p["build"] = ws
	for mi in (p["node"] as Node3D).find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		for k in range(m.get_blend_shape_count()):
			m.set_blend_shape_value(k, 0.0)
		for n in ws:
			var k := m.find_blend_shape_by_name(n)
			if k >= 0:
				m.set_blend_shape_value(k, float(ws[n]))
	_move_joints(p, morphs, ws)


## Every joint moved by the blend of the corners' moves (skeleton space); each bone keeps its rest
## turn, so a clip's rotations mean what they did. The hips' travel in every clip scales with his
## legs (Skeleton3D.motion_scale), as mh_to_glb did for the average body.
static func _move_joints(p: Dictionary, morphs: Dictionary, ws: Dictionary) -> void:
	var skel: Skeleton3D = p["skel"]
	if not p.has("rest0"):
		var r := []
		for b in range(skel.get_bone_count()):
			r.append(skel.get_bone_rest(b))
		p["rest0"] = r
	var rest0: Array = p["rest0"]
	var moved := {}
	var leg := 1.0
	for n in ws:
		if not morphs.has(n):
			continue
		var w := float(ws[n])
		var m: Dictionary = morphs[n]
		leg += w * (float(m.get("leg", 1.0)) - 1.0)
		var dd: Dictionary = m.get("d", {})
		for bn in dd:
			var v: Array = dd[bn]
			moved[bn] = moved.get(bn, Vector3.ZERO) + Vector3(v[0], v[1], v[2]) * w
	# Global rest turns of the untouched rig (only origins change below).
	var basis := []
	for b in range(skel.get_bone_count()):
		var t: Transform3D = rest0[b]
		var up := skel.get_bone_parent(b)
		basis.append((basis[up] as Basis) * t.basis if up >= 0 else t.basis)
	for b in range(skel.get_bone_count()):
		var t: Transform3D = rest0[b]
		var up := skel.get_bone_parent(b)
		var mine: Vector3 = moved.get(skel.get_bone_name(b), Vector3.ZERO)
		var theirs: Vector3 = moved.get(skel.get_bone_name(up), Vector3.ZERO) if up >= 0 else Vector3.ZERO
		var pb: Basis = basis[up] if up >= 0 else Basis.IDENTITY
		skel.set_bone_rest(b, Transform3D(t.basis, t.origin + pb.inverse() * (mine - theirs)))
	skel.reset_bone_poses()
	skel.motion_scale = leg
	p["leg"] = leg
