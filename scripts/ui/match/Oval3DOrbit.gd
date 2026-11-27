class_name Oval3DOrbit
extends RefCounted
## The aerial orbit: a camera circling the outside of the ground as if from a helicopter (row 202,
## director 2026-11-27: "an orbiting helicopter view shot of each oval going around the exterior of
## the ground, so anything that camera sees has to look good"). There is no real TV helicopter to
## copy (director, same day: "it was a turn of phrase"), so the shot is a cinematic one: the stadium
## held in the middle of the picture with its streets, its skyline and its hills round it, the camera
## moving at an even pace on one smooth circle and never passing through anything.
##
## Everything is measured off the ground as it is loaded (plan()), so one path fits every ground:
##   - a height map of everything the match draws (stadium, its neighbours, the backdrop), CELL m square,
##     and one of the stadium's own model alone (its .glb files and seats, not its neighbours);
##   - the stadium's own outline: from the boundary fence outward, the last of its model standing EDGE_H m
##     or more before an open gap of EDGE_GAP m;
##   - the circle: ORBIT_K times the stadium's outer radius, round the outline's middle;
##   - the height: one height for the lap, the stadium's middle seen LOOK_DOWN degrees below level,
##     raised (at most SIGHT_MAX times) so that round SIGHT_SHARE of the circle no tower in the near part of
##     the picture (the nearer FORE of the way from the stadium to the camera) stands over the line to
##     the stadium's roof line or its middle. Buildings beside the stadium may hide its foot, as they
##     do from the air over a real city. Wherever anything stands within CLEAR_R m of the path the
##     camera climbs to clear it by CLEARANCE m, the climb eased over EASE_DEG degrees, never a jump;
##   - the lens: the stadium's outer width fills FILL of the picture's width, so its surroundings show
##     on both sides; the camera tilts up a little so the stadium's middle sits SIT of the way down the
##     picture, with the skyline and the sky above it (on a phone's tall picture, more sky).
## Looks only: nothing in play reads it.

const CELL := 4.0            # m: the height map's square
const EDGE_H := 6.0          # m above the turf: taller is stadium (or a neighbour), lower is open ground
const EDGE_GAP := 20.0       # m of open ground that ends the stadium
const EDGE_REACH := 450.0    # m from the middle the stadium's outline is looked for
const ORBIT_K := 3.2         # the circle's radius over the stadium's outer radius (a long lens, as from a helicopter)
const LOOK_DOWN := 20.0      # degrees below level to the stadium's middle, before any raise
const AIM_UP := 0.3          # the camera aims this share of the stadium's height above the turf
const CLEAR_R := 30.0        # m round the camera's path that must stand clear below it
const CLEARANCE := 20.0      # m the camera passes over anything near its path
const SIGHT_CLEAR := 4.0     # m the line to the stadium passes over anything between
const EASE_DEG := 40.0       # degrees of circle a raise is eased over (each side)
const SIGHT_MAX := 1.4       # the flying height is raised for towers in the view at most this many times
const SIGHT_SHARE := 0.75    # ...so that this share of the circle has no tower looming in front
const FORE := 0.85           # the share of the way to the camera, nearest it, kept clear of the view
const FILL := 0.5            # the stadium's outer width over the picture's width
const SIT := 0.62            # the stadium's middle sits this far down the picture (0 top, 1 bottom): sky and skyline over it
const SIT_MAX := 0.68        # ...or as far as this, to keep the horizon HORIZON degrees under the picture's top
const HORIZON := 1.5         # degrees
const LAP_S := 72.0          # s for one lap (5 degrees a second)
const SAMPLES := 360         # the circle is planned at each degree
const ANGLES := 180          # directions the stadium's outline is measured in

var centre := Vector3.ZERO   # the stadium's middle on the turf (world)
var radius := 0.0            # the circle's radius
var r_out := 0.0             # the stadium's outer radius (its widest)
var top := 0.0               # the stadium's highest point (roof, light towers) above the turf
var aim := Vector3.ZERO      # where the camera looks
var heights := PackedFloat32Array()   # the camera's height at each degree of the circle
var fov := 40.0              # horizontal field of view (the camera keeps its width)
var outline := PackedFloat32Array()   # the stadium's outer distance in each of ANGLES directions
var _h := {}                 # Vector2i cell -> highest point (m)
var _hs := {}                # the same for the stadium's own model


## The orbit for the ground `root` (the Oval3D, or any node holding the ground), measured off its meshes.
## `fence` is the boundary's half length and half width (GroundModels.match_fence()); `slug` the ground's
## model folder, which names the stadium's own model under the Ground node.
static func plan(root: Node3D, fence: Vector2, slug: String) -> Oval3DOrbit:
	var o := Oval3DOrbit.new()
	o._h = _height_map(root)
	var own: Array = []
	for gr in root.find_children("Ground", "Node3D", true, false):
		for c in gr.get_children():
			if str(c.name).begins_with(slug) or str(c.name).to_lower().contains("seat"):
				own.append(c)
	for c: Node3D in own:
		var hm := _height_map(c)
		for k in hm:
			o._hs[k] = maxf(float(o._hs.get(k, -INF)), float(hm[k]))
	if o._hs.is_empty():   # a model not laid by GroundModels (a draft): its whole height map
		o._hs = o._h
	o._stadium(fence)
	o._circle()
	return o


## Where the camera is and where it looks `t` seconds into the orbit (0 starts due east of the middle,
## turning anticlockwise seen from above).
func at(t: float) -> Transform3D:
	var deg := fposmod(t / LAP_S * 360.0, 360.0)
	var a := deg_to_rad(deg)
	var i := int(floorf(deg)) % SAMPLES
	var f := deg - floorf(deg)
	var y := lerpf(heights[i], heights[(i + 1) % SAMPLES], f)
	var eye := centre + Vector3(cos(a) * radius, 0.0, -sin(a) * radius)
	eye.y = y
	return Transform3D(Basis.looking_at(aim - eye, Vector3.UP), eye)


## Puts `cam` on the orbit `t` seconds in, tilted up so the stadium sits SIT of the way down its picture.
func place(cam: Camera3D, t: float) -> void:
	cam.keep_aspect = Camera3D.KEEP_WIDTH
	cam.fov = fov
	cam.near = 1.0
	var size := cam.get_viewport().get_visible_rect().size
	var tall := size.y / maxf(size.x, 1.0)
	# The picture's half height as a tangent; the middle at SIT down is this far below the centre line.
	var half_v := tan(deg_to_rad(fov) * 0.5) * tall
	var xf := at(t)
	var down := -(xf.basis * Vector3.FORWARD).y   # sine of the look down to the aim
	var pitch := asin(clampf(down, -1.0, 1.0))
	var tilt := atan((SIT - 0.5) * 2.0 * half_v)
	# Tilt further, up to SIT_MAX, until the horizon is in the picture.
	var top_edge := atan(half_v) + tilt - pitch
	if top_edge < deg_to_rad(HORIZON):
		tilt = minf(tilt + deg_to_rad(HORIZON) - top_edge, atan((SIT_MAX - 0.5) * 2.0 * half_v))
	cam.global_transform = Transform3D(xf.basis.rotated(xf.basis.x, tilt), xf.origin)


func _cell(x: float, z: float) -> Vector2i:
	return Vector2i(floori(x / CELL), floori(z / CELL))


func height_at(x: float, z: float) -> float:
	return float(_h.get(_cell(x, z), 0.0))


func _own_at(x: float, z: float) -> float:
	return float(_hs.get(_cell(x, z), 0.0))


## The highest point within `r` m of (x, z).
func highest_near(x: float, z: float, r: float) -> float:
	var c := _cell(x, z)
	var n := int(ceil(r / CELL))
	var best := 0.0
	for dx in range(-n, n + 1):
		for dz in range(-n, n + 1):
			if dx * dx + dz * dz > (n + 1) * (n + 1):
				continue
			best = maxf(best, float(_h.get(c + Vector2i(dx, dz), 0.0)))
	return best


static func _put(h: Dictionary, p: Vector3) -> void:
	var c := Vector2i(floori(p.x / CELL), floori(p.z / CELL))
	if p.y > float(h.get(c, -INF)):
		h[c] = p.y


static func _height_map(root: Node3D) -> Dictionary:
	var h := {}
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		# Not the men, the ball or the picture's film (skinned or primitive meshes): only what stands.
		if mi.mesh == null or not mi.is_visible_in_tree() or mi.skin != null or mi.mesh is PrimitiveMesh:
			continue
		var xf := mi.global_transform
		for s in mi.mesh.get_surface_count():
			var arr := mi.mesh.surface_get_arrays(s)
			if arr.is_empty() or arr[Mesh.ARRAY_VERTEX] == null:
				continue
			for v: Vector3 in arr[Mesh.ARRAY_VERTEX]:
				_put(h, xf * v)
	for mm: MultiMeshInstance3D in root.find_children("*", "MultiMeshInstance3D", true, false):
		if mm.multimesh == null or mm.multimesh.mesh == null or not mm.is_visible_in_tree():
			continue
		var box := mm.multimesh.mesh.get_aabb()
		var xf := mm.global_transform
		for k in mm.multimesh.visible_instance_count if mm.multimesh.visible_instance_count >= 0 else mm.multimesh.instance_count:
			var it := xf * mm.multimesh.get_instance_transform(k)
			# The instance's top at its middle: enough for a tree, a seat or a lamp.
			var mid := it * (box.position + box.size * Vector3(0.5, 1.0, 0.5))
			_put(h, mid)
	return h


## The stadium's outline, outer radius, top and middle.
func _stadium(fence: Vector2) -> void:
	outline.resize(ANGLES)
	# The middle is the oval's: the match lays every model with its boundary centred there.
	centre = Vector3.ZERO
	for k in ANGLES:
		var a := TAU * k / ANGLES
		var d := Vector2(cos(a), -sin(a))
		# From the fence (an ellipse along x) outward.
		var start := 1.0 / sqrt(pow(d.x / fence.x, 2) + pow(d.y / fence.y, 2))
		var edge := start
		var r := start
		while r < EDGE_REACH:
			if _own_at(d.x * r, d.y * r) >= EDGE_H:
				edge = r
			elif r - edge >= EDGE_GAP:
				break
			r += CELL * 0.5
		outline[k] = edge
	var sorted := Array(outline)
	sorted.sort()
	r_out = float(sorted[int(ANGLES * 0.95)])
	top = 0.0
	for c: Vector2i in _hs:
		var p := (Vector2(c) + Vector2(0.5, 0.5)) * CELL
		var k := int(round(fposmod(atan2(-p.y, p.x), TAU) / TAU * ANGLES)) % ANGLES
		if p.length() <= outline[k]:
			top = maxf(top, float(_hs[c]))


func _circle() -> void:
	radius = ORBIT_K * r_out
	aim = centre + Vector3(0.0, top * AIM_UP, 0.0)
	var base := aim.y + radius * tan(deg_to_rad(LOOK_DOWN))
	# One flying height for the whole lap, as a helicopter holds its height: raised for the towers in
	# the foreground of the view where SIGHT_SHARE of the circle needs it, never above SIGHT_MAX
	# times the base. Where one stretch alone has a tower in front, the tower stays in the picture, as
	# it would from the air.
	var sight := []
	for i in SAMPLES:
		var a := deg_to_rad(float(i))
		var eye := Vector3(centre.x + cos(a) * radius, base, centre.z - sin(a) * radius)
		for step in 40:
			var lift := _sight_lift(eye, a)
			if lift <= 0.0:
				break
			eye.y += lift
		sight.append(eye.y)
	sight.sort()
	var cruise := clampf(float(sight[int(SAMPLES * SIGHT_SHARE)]), base, base * SIGHT_MAX)
	# Over anything within CLEAR_R m of the path the camera must climb (never passes through).
	var need := PackedFloat32Array()
	need.resize(SAMPLES)
	for i in SAMPLES:
		var a := deg_to_rad(float(i))
		need[i] = maxf(cruise, highest_near(centre.x + cos(a) * radius, centre.z - sin(a) * radius, CLEAR_R) + CLEARANCE)
	base = cruise
	# Ease each raise round the circle: the height at each degree is the most any raise within
	# EASE_DEG degrees asks of it, falling off as a cosine with the distance in degrees.
	heights.resize(SAMPLES)
	var span := int(EASE_DEG)
	for i in SAMPLES:
		var y := base
		for j in range(-span, span + 1):
			var w := 0.5 + 0.5 * cos(PI * float(j) / float(span))
			y = maxf(y, base + (need[(i + j + SAMPLES) % SAMPLES] - base) * w)
		heights[i] = y
	# The lens: the stadium's outer width at FILL of the picture's width, from the circle's mean height.
	var mean := 0.0
	for y in heights:
		mean += y
	mean /= SAMPLES
	var dist := Vector2(radius, mean - aim.y).length()
	fov = rad_to_deg(2.0 * atan(r_out / (FILL * dist)))


## How much higher the camera at `eye` (on the circle at angle `a`) must go so its lines to the
## stadium's near side (its roof line half way up, across the near half of the picture) and to the aim
## pass over everything outside the stadium; 0 when they already do.
func _sight_lift(eye: Vector3, a: float) -> float:
	var worst := 0.0
	for off in [-50.0, -25.0, 0.0, 25.0, 50.0]:
		var b := fposmod(a + deg_to_rad(off), TAU)
		var k := int(round(b / TAU * ANGLES)) % ANGLES
		var edge := Vector3(cos(b) * outline[k], top, -sin(b) * outline[k])
		worst = maxf(worst, _line_lift(eye, edge))
	return maxf(worst, _line_lift(eye, aim))


## How much higher `eye` must go so the line from `to` to it passes SIGHT_CLEAR m over everything on the
## nearer FORE of the way, to within CLEAR_R m of the eye.
func _line_lift(eye: Vector3, to: Vector3) -> float:
	var flat := Vector2(eye.x - to.x, eye.z - to.z).length()
	var worst := 0.0
	var s := flat * (1.0 - FORE)
	while s < flat - CLEAR_R:
		var f := s / flat
		var p := to.lerp(eye, f)
		if _own_at(p.x, p.z) < EDGE_H:   # the stadium's own roof may cross its own line
			var over := height_at(p.x, p.z) + SIGHT_CLEAR - p.y
			if over > 0.0:
				# Raising the eye by dy raises the line here by dy * f.
				worst = maxf(worst, over / maxf(f, 0.05))
		s += CELL
	return worst
