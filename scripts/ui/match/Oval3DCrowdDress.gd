class_name Oval3DCrowdDress
extends RefCounted
## What each part of a crowd body can wear (row 202 2c, the MCG crowd brought up to standard,
## 2026-11-21). The baked bodies (Oval3DCrowdSet) are dressed for summer: a t-shirt, shorts, bare
## arms and shins, and one man is bald. A winter footy crowd wears jackets, jeans, scarves and
## beanies, so each vertex is sorted once, from the body's seated pose (the first idle frame), into
## a part the shaders can dress differently for each supporter:
##   0 as baked (top, pants, skin, hair or shoes, by the vertex colour)
##   1 arm: bare skin of the arm; a long sleeve covers it down to its hand
##     (UV2.x: how far the vertex is from them, in hands: under 1 is the hand; 10 on the top,
##     0 elsewhere)
##   2 shin: bare skin that long trousers cover
##   3 neck: the top round his neck, where a scarf sits
##   4 scalp: skin on top of the head, where short hair or a beanie sits
## The part goes in each vertex's UV.y (UV.x already holds its column in the animation table).
## Looks only: nothing here reads the match.

const ARM := 1
const SHIN := 2
const NECK := 3
const SCALP := 4

## How far below his collar the scarf reaches (m), and how far from the neck's middle.
const SCARF_DROP := 0.075
const SCARF_WIDE := 0.12
## The hand: this much of each arm's end (m, a man's; a child's scales with his height) stays
## bare under a long sleeve (the shaders cut it there).
const HAND := 0.15
const HAND_SHARE := 0.45
## The scalp: skin this far below the top of the head (m) and above his ears.
const SCALP_DROP := 0.085
## The hands-on-head clip, HANDS_UP s in (both hands at his head), and how far (m) a vertex must
## move between the idle and that moment to be part of an arm.
const HANDS_UP := 2.3
const MOVED := 0.12
## Arm skin within this (m) of the top is where the arm comes out of it, unless it is within LAP
## of the top's hem (his hands resting in his lap touch the top too).
const SLEEVE := 0.04
const LAP := 0.1


## Each body's sorting, done once a run (a few hundred vertices a body).
static var _done := {}


## body: one of Oval3DCrowdSet.bodies. Returns {mesh: the body's mesh with each vertex's part in
## UV.y, torso: Vector2(waist y, collar y) in the body's metres, legs: the pants' lowest point,
## neck: the collar's height, top: the top of the head, foot: the soles, and the two sitting
## clips between the idle and the cheer, each Vector2i(row, frames): head (both hands to his head,
## the near miss) and pump (one arm up, a fist pump)}.
static func dress(body: Dictionary) -> Dictionary:
	var key := "%s:%d" % [str(body.get("name", "")), (body["mesh"] as Mesh).get_instance_id()]
	if not _done.has(key):
		_done[key] = _dress(body)
	return _done[key]


static func _dress(body: Dictionary) -> Dictionary:
	var src: ArrayMesh = body["mesh"]
	var a := src.surface_get_arrays(0)
	var uv: PackedVector2Array = a[Mesh.ARRAY_TEX_UV]
	var col: PackedColorArray = a[Mesh.ARRAY_COLOR]
	var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
	var img: Image = (body["pos_tex"] as Texture2D).get_image()
	var row := int((body["idle"] as Vector2i).x)
	var n := uv.size()
	var p := PackedVector3Array()
	p.resize(n)
	for i in n:
		var c := img.get_pixel(int(uv[i].x), row)
		p[i] = Vector3(c.r, c.g, c.b)
	var role := PackedInt32Array()   # 0 top, 1 pants, 2 skin, 3 hair, 4 shoes
	role.resize(n)
	var top_lo := INF
	var top_hi := -INF
	var pants_lo := INF
	var head_hi := -INF
	var foot_lo := INF
	for i in n:
		var c := col[i]
		role[i] = 0 if c.r > 0.5 else (1 if c.g > 0.5 else (2 if c.b > 0.5 else (3 if c.a > 0.5 else 4)))
		foot_lo = minf(foot_lo, p[i].y)
		head_hi = maxf(head_hi, p[i].y)
		if role[i] == 0:
			top_lo = minf(top_lo, p[i].y)
			top_hi = maxf(top_hi, p[i].y)
		elif role[i] == 1:
			pants_lo = minf(pants_lo, p[i].y)
	if pants_lo == INF:
		pants_lo = top_lo
	var scale := (head_hi - foot_lo) / 1.3   # a seated man is about 1.3 m from heel to crown
	# The neck's middle: the skin just above the collar.
	var neck := Vector3.ZERO
	var nn := 0
	for i in n:
		if role[i] == 2 and p[i].y > top_hi - 0.02 and p[i].y < top_hi + 0.08 * scale:
			neck += p[i]
			nn += 1
	neck = neck / float(maxi(1, nn))
	# The head: skin above the collar, near the neck's line (not a hand raised to it).
	var head := PackedByteArray()
	head.resize(n)
	for i in n:
		var flat := Vector2(p[i].x - neck.x, p[i].z - neck.z).length()
		head[i] = 1 if role[i] == 2 and p[i].y > top_hi - 0.04 * scale and flat < 0.16 * scale else 0
	# Arms from legs: in the second sitting clip he raises both hands to his head and his legs stay
	# put, so the bare skin below his collar that moves is his arms.
	var rest_a := int((body["idle"] as Vector2i).y) + int(round(HANDS_UP * float(body["fps"])))
	var arm := PackedByteArray()
	arm.resize(n)
	for i in n:
		var c := img.get_pixel(int(uv[i].x), rest_a)
		if role[i] == 2 and head[i] == 0 and p[i].y < top_hi - 0.04 * scale \
				and p[i].distance_to(Vector3(c.r, c.g, c.b)) > MOVED * scale:
			arm[i] = 1
	# Along each arm, over the mesh's edges, from where it comes out of the top (the skin within
	# SLEEVE of it) to the fingertips: the hand is the last HAND of that way.
	var along := _along_arm(p, idx, role, arm, scale, top_lo + LAP * scale)
	var part := PackedFloat32Array()
	part.resize(n)
	for i in n:
		var k := 0
		if role[i] == 2 and head[i] == 1:
			if p[i].y > head_hi - SCALP_DROP * scale and p[i].y > neck.y + 0.12 * scale:
				k = SCALP
		elif arm[i] == 1:
			k = ARM
		elif role[i] == 2 and p[i].y < neck.y - 0.3 * scale:
			k = SHIN
		elif role[i] == 0 and p[i].y > top_hi - SCARF_DROP * scale \
				and Vector2(p[i].x - neck.x, p[i].z - neck.z).length() < SCARF_WIDE * scale:
			k = NECK
		part[i] = k
	# A child's collar sits wider and lower than a man's: if nothing was found round the neck, look
	# lower and wider once.
	if not part.has(float(NECK)):
		for i in n:
			if role[i] == 0 and p[i].y > top_hi - SCARF_DROP * 1.8 * scale \
					and Vector2(p[i].x - neck.x, p[i].z - neck.z).length() < SCARF_WIDE * 1.6 * scale:
				part[i] = NECK
	# How far each arm vertex is from its fingertips, in hands: a sleeve reaches down to 1. The
	# clothes count as far up the arm, everything else as none.
	var uv2 := PackedVector2Array()
	uv2.resize(n)
	for i in n:
		uv[i].y = part[i]
		var from_tip := 0.0
		if arm[i] == 1:
			var far: float = along[1][i]
			# Where the bare arm is short (a sleeve already to the elbow), the hand is less of it.
			from_tip = (far - along[0][i]) / maxf(0.01, minf(HAND * scale, far * HAND_SHARE))
		elif role[i] == 0:
			from_tip = 10.0
		uv2[i] = Vector2(from_tip, 0.0)
	a[Mesh.ARRAY_TEX_UV] = uv
	a[Mesh.ARRAY_TEX_UV2] = uv2
	var out := ArrayMesh.new()
	out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	out.custom_aabb = src.custom_aabb if src.custom_aabb.size != Vector3.ZERO else src.get_aabb().grow(1.0)
	var clips := _clips(img, uv, body)
	return {"mesh": out, "torso": Vector2(top_lo, top_hi), "legs": pants_lo, "neck": top_hi,
			"top": head_hi, "foot": foot_lo, "head": clips[0], "pump": clips[1]}


## The baked table holds four sitting clips: the idle, then two more, then the cheer
## (bake_crowd_vat.py), but the set (Oval3DCrowdSet) names only the first and the last. The two
## between both start and end seated at rest, so the second begins where the pose comes closest
## to that rest, in the later half of the rows between.
static func _clips(img: Image, uv: PackedVector2Array, body: Dictionary) -> Array:
	var r0 := int((body["idle"] as Vector2i).y)
	var r1 := int((body["cheer"] as Vector2i).x)
	var far := func(r: int) -> float:
		var s := 0.0
		for i in range(0, uv.size(), 3):
			var a := img.get_pixel(int(uv[i].x), r)
			var b := img.get_pixel(int(uv[i].x), r0)
			s += Vector3(a.r - b.r, a.g - b.g, a.b - b.b).length()
		return s
	var best := r0 + (r1 - r0) / 2
	var low := INF
	for r in range(r0 + (r1 - r0) / 2, r1 - 10):
		var f: float = far.call(r)
		if f < low:
			low = f
			best = r
	# The rest lasts a few frames: the second clip starts at its end.
	while best + 1 < r1 - 10 and float(far.call(best + 1)) < low * 1.03 + 0.05:
		best += 1
	return [Vector2i(r0, best - r0), Vector2i(best, r1 - best)]

## [distance along the arm from the top to each arm vertex, the arm's whole length at each arm
## vertex] (m), over the mesh's edges through the arm's own vertices. Only skin higher than
## `above` starts an arm.
static func _along_arm(p: PackedVector3Array, idx: PackedInt32Array, role: PackedInt32Array, arm: PackedByteArray, scale: float, above: float) -> Array:
	var n := p.size()
	var nb := []
	nb.resize(n)
	for i in n:
		nb[i] = []
	for t in range(0, idx.size(), 3):
		for k in 3:
			var u := idx[t + k]
			var v := idx[t + (k + 1) % 3]
			if arm[u] == 1 and arm[v] == 1:
				nb[u].append(v)
				nb[v].append(u)
	var d := PackedFloat32Array()
	d.resize(n)
	var done := PackedByteArray()
	done.resize(n)
	for i in n:
		d[i] = INF
		if arm[i] == 0 or p[i].y < above:
			continue
		for j in n:
			if role[j] == 0 and p[i].distance_to(p[j]) < SLEEVE * scale:
				d[i] = 0.0
				break
	while true:
		var best := -1
		for i in n:
			if done[i] == 0 and d[i] < INF and (best < 0 or d[i] < d[best]):
				best = i
		if best < 0:
			break
		done[best] = 1
		for j: int in nb[best]:
			d[j] = minf(d[j], d[best] + p[best].distance_to(p[j]))
	# Each arm (connected over its edges) and its length: its furthest point from the top.
	var far := PackedFloat32Array()
	far.resize(n)
	var seen := PackedByteArray()
	seen.resize(n)
	for s in n:
		if arm[s] == 0 or seen[s] == 1:
			continue
		var group := [s]
		seen[s] = 1
		var at := 0
		var longest := 0.0
		while at < group.size():
			var u: int = group[at]
			at += 1
			if d[u] < INF:
				longest = maxf(longest, d[u])
			for v: int in nb[u]:
				if seen[v] == 0:
					seen[v] = 1
					group.append(v)
		for u: int in group:
			far[u] = longest
			if d[u] == INF:
				d[u] = longest
	return [d, far]
