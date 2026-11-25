class_name Oval3DTowers
extends Node3D
## A ground's light towers at night (rule 2.82; row 202 2a): one floodlight from each of the
## model's own lamp banks (the MCG's six towers, wherever the model put them), their heads
## glowing against the sky, and the row of lights along the roof's edge that a night broadcast
## shows under every stand. Looks only (rule 1.29): nothing here reads or writes the match.
##
## Each bank lights the ground in two parts. Its beam (a light from the tower's direction, the
## same across the ground) throws the men's shadows, one away from each tower: the star of faint
## shadows a night game is known by. Its spill (a spotlight from the head itself) is brighter on
## the side of the ground nearer the tower, as under real towers, and throws no shadow. A phone
## draws a shadow map of the men for each beam that throws one, so the graphics level
## (Oval3DQuality "tower_shadows") says how many do; a tower without a shadowed beam lights by
## its spill alone. Only the men, the umpires and the ball throw a tower's shadow: the stands
## have their roofs' own, and the whole stadium in every tower's shadow map would cost dearly.
## A roofed ground (rule 2.91) and a ground whose model has no lamps keep Oval3DTurf's own
## night light: `banks` is empty and the turf never turns this on.

## A lamp surface: its material's name in the ground model (each ground's builder named its own).
const LAMP_NAME := "^(t_)?(close_)?lamps?(_face|_lens)?$"
## Lit from their roofs (rule 2.91): no towers.
const ROOF_LIT := ["marvel", "optus"]
## Lamps further apart round the ground than this start another bank.
const BANK_GAP := deg_to_rad(9.0)
## The towers' light: near white, as the MCG's LEDs read on TV.
const LAMP_COLOUR := Color(1.0, 0.99, 0.96)
## How fast a spill fades with distance (Godot's falloff exponent): 1/d^ATTEN. Real floodlights
## fall off with the square, but each is aimed so the far side gets its brightest beams; this
## keeps a gentle pool nearer each tower without dark patches between.
const ATTEN := 0.55
## The light the towers together put on the middle of the ground. Measured with
## tools/visual/capture_night3d.gd: open grass under the MCG's towers a little brighter and
## yellower than a fine day's (rule 2.81), as lit turf reads on a night broadcast.
const CENTRE_LIGHT := 1.5
## The share of all the towers' light carried by the shadow-throwing beams, by how many throw
## one (the rest is every tower's spill). Each shadow takes its beam's light out of the turf
## behind a man, so with a few beams carrying most of the light each shadow reads, faintly, and
## where they all cross at his boots he stands in a dark pool, as on a night broadcast.
const BEAM_SHARE := {0: 0.0, 1: 0.55, 2: 0.7, 3: 0.8, 4: 0.85}
## How far up the lights are before the beams take over from the spill (the sun has gone).
const BEAMS_FROM := 0.5
## How far from the camera a beam's shadows reach (m): the men in the broadcast picture.
const SHADOW_REACH := 90.0
## The glow round each head (m across) and the roof-line lights (m across, m apart).
const GLOW_SIZE := 34.0
## The glows are light added over the finished picture: drawn after the broadcast film (which
## redraws the screen and would paint over anything see-through drawn before it), like the club
## rings, and still hidden behind a stand or a roof in front of them.
const GLOW_PRIORITY := Material.RENDER_PRIORITY_MAX
const DOT_SIZE := 1.6
const DOT_EVERY := 3.0

var slug := ""
var banks: Array[Vector3] = []      # each bank's middle, in the oval's space
var spots: Array[SpotLight3D] = []  # each bank's spill
var beams: Array[DirectionalLight3D] = []  # each bank's beam
var _light: Array[float] = []       # the light each bank puts on the middle of the ground
var _spill_k: Array[float] = []     # a spill's energy for one unit of light on the middle
var _beam_k: Array[float] = []      # a beam's energy for one unit
var _order: Array[int] = []         # the banks in the order they get a shadow, spread round
var _glows: Array[MeshInstance3D] = []
var _lamps: Array = []              # [MeshInstance3D, surface, lit material] of every lamp face
var _glow_mat: ShaderMaterial
var _roofline: MultiMeshInstance3D
var _shadows := 4
var level := 0.0


## The towers for a ground model laid in `oval` (GroundModels.instantiate's root).
func build(p_slug: String, model: Node3D, oval: Node3D) -> void:
	slug = p_slug
	name = "Towers"
	if slug in ROOF_LIT or model == null:
		return
	var pts := _lamp_points(model, oval)
	banks = bank_middles(pts)
	if banks.is_empty():
		return
	_glow_mat = ShaderMaterial.new()
	_glow_mat.shader = preload("res://scripts/ui/match/oval3d_glow.gdshader")
	_glow_mat.render_priority = GLOW_PRIORITY
	var target := Vector3.ZERO
	for b in banks:
		var s := SpotLight3D.new()
		s.light_color = LAMP_COLOUR
		s.position = b
		add_child(s)
		s.look_at(target, Vector3.UP)
		# Wide enough that its beam takes in the whole ground, the far pocket included.
		var widest := 0.0
		var far := 0.0
		for i in 32:
			var a := TAU * i / 32.0
			var p := Vector3(cos(a) * GroundModels.match_fence().x, 0.0, sin(a) * GroundModels.match_fence().y)
			widest = maxf(widest, rad_to_deg((p - b).angle_to(target - b)))
			far = maxf(far, b.distance_to(p))
		s.spot_angle = minf(widest + 6.0, 89.0)
		s.spot_angle_attenuation = 0.35
		s.spot_range = far + 40.0
		s.spot_attenuation = ATTEN
		s.shadow_enabled = false
		spots.append(s)
		var d := b.length()
		var cos_in := b.y / d
		_light.append(CENTRE_LIGHT / banks.size())
		_spill_k.append(1.0 / (cos_in * pow(d, -ATTEN)))
		var beam := DirectionalLight3D.new()
		beam.light_color = LAMP_COLOUR
		add_child(beam)
		beam.basis = Basis.looking_at(-b.normalized(), Vector3.UP)
		beam.shadow_enabled = true
		# Two bands: a single band drawn for several lights at once lost the men's shadows.
		beam.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		beam.directional_shadow_max_distance = SHADOW_REACH
		beam.shadow_normal_bias = 2.0
		beam.shadow_caster_mask = SHADOW_LAYER
		beam.visible = false
		_beam_k.append(1.0 / cos_in)
		beams.append(beam)
		var g := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(GLOW_SIZE, GLOW_SIZE)
		g.mesh = q
		g.material_override = _glow_mat
		g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		g.position = b
		add_child(g)
		_glows.append(g)
	_order = spread_order(banks)
	_roofline = _roof_lights(model, oval)
	set_level(0.0)


## The banks in an order that spreads the first few round the ground: each next one the bank
## furthest (by bearing) from those already taken.
static func spread_order(p_banks: Array[Vector3]) -> Array[int]:
	var out: Array[int] = []
	if p_banks.is_empty():
		return out
	out.append(0)
	while out.size() < p_banks.size():
		var best := -1
		var best_gap := -1.0
		for i in p_banks.size():
			if i in out:
				continue
			var gap := INF
			for j in out:
				var a := atan2(p_banks[i].z, p_banks[i].x) - atan2(p_banks[j].z, p_banks[j].x)
				gap = minf(gap, absf(wrapf(a, -PI, PI)))
			if gap > best_gap:
				best_gap = gap
				best = i
		out.append(best)
	return out


## The visual layer the shadow-throwing men sit on (besides the camera's layer 1).
const SHADOW_LAYER := 1 << 19


## Put a node and everything under it on the towers' shadow layer.
static func throws_shadow(n: Node) -> void:
	if n is VisualInstance3D:
		n.layers |= SHADOW_LAYER
	for c in n.get_children():
		throws_shadow(c)


## How many towers throw the men's shadows (Oval3DQuality "tower_shadows"), at most four (the
## renderer draws four directional shadows at once).
func set_shadows(n: int) -> void:
	_shadows = clampi(n, 0, 4)
	set_level(level)


## How far the lights are up: 0 off, 1 a night game. The heads glow whenever they are on.
func set_level(k: float) -> void:
	level = clampf(k, 0.0, 1.0)
	var on := level > 0.001
	var total := 0.0
	for x in _light:
		total += x
	# The beams throw their shadows once the towers carry the light (a twilight game's sun still
	# throws its own, and the renderer draws only so many shadowed lights at once).
	var n := _shadows if level >= BEAMS_FROM else 0
	var share: float = BEAM_SHARE.get(n, 0.0)
	for j in _order.size():
		var i: int = _order[j]
		var beam := j < n
		spots[i].visible = on
		spots[i].light_energy = total * (1.0 - share) / banks.size() * _spill_k[i] * level
		beams[i].visible = on and beam
		beams[i].light_energy = (total * share / n if beam else 0.0) * _beam_k[i] * level
	for g in _glows:
		g.visible = on
	if _glow_mat != null:
		_glow_mat.set_shader_parameter("strength", minf(1.0, level * 4.0))
	if _roofline != null:
		_roofline.visible = on
	for l in _lamps:
		(l[0] as MeshInstance3D).set_surface_override_material(int(l[1]), l[2] if on else null)


## Every lamp vertex of the model, in the oval's space; the lamp surfaces kept to light up.
func _lamp_points(model: Node3D, oval: Node3D) -> PackedVector3Array:
	var re := RegEx.create_from_string(LAMP_NAME)
	var out := PackedVector3Array()
	var to_oval := oval.global_transform.affine_inverse()
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null:
			continue
		var xf := to_oval * mi.global_transform
		for si in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(si)
			if m == null or re.search(m.resource_name.to_lower()) == null:
				continue
			_lamps.append([mi, si, _lit(m)])
			var verts: PackedVector3Array = mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
			for v in verts:
				out.append(xf * v)
	return out


## A lamp face switched on: its own pattern (the rows of lamps the builder drew), glowing.
static func _lit(m: Material) -> Material:
	var lit := ShaderMaterial.new()
	lit.shader = preload("res://scripts/ui/match/oval3d_lamp.gdshader")
	if m is BaseMaterial3D and (m as BaseMaterial3D).albedo_texture != null:
		lit.set_shader_parameter("pattern", (m as BaseMaterial3D).albedo_texture)
		lit.set_shader_parameter("has_pattern", true)
	return lit


## The lamp banks: lamps grouped by their bearing round the ground's middle, a gap of more than
## BANK_GAP starting a new bank. Each bank's middle is the mean of its lamps.
static func bank_middles(pts: PackedVector3Array) -> Array[Vector3]:
	var out: Array[Vector3] = []
	if pts.is_empty():
		return out
	var by := []
	for p in pts:
		by.append([atan2(p.z, p.x), p])
	by.sort_custom(func(a, b): return a[0] < b[0])
	var groups := [[by[0]]]
	for i in range(1, by.size()):
		if by[i][0] - by[i - 1][0] > BANK_GAP:
			groups.append([])
		groups[-1].append(by[i])
	# The first and last groups meet across the back of the circle.
	if groups.size() > 1 and by[0][0] + TAU - by[-1][0] <= BANK_GAP:
		groups[0].append_array(groups.pop_back())
	for g in groups:
		var sum := Vector3.ZERO
		for e in g:
			sum += e[1]
		var mid: Vector3 = sum / g.size()
		# A stray lamp or two (a gate lamp low on a wall) is not a tower.
		if g.size() >= 8 and mid.y > 15.0:
			out.append(mid)
	return out


## The lights along the roof's front edge: at each step round the ground, the roof's point
## nearest the ground's middle, a small bright light just under it. None where no roof is.
func _roof_lights(model: Node3D, oval: Node3D) -> MultiMeshInstance3D:
	const BUCKETS := 720
	var best := []
	best.resize(BUCKETS)
	var to_oval := oval.global_transform.affine_inverse()
	var f: Vector2 = GroundModels.match_fence()
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if mi.mesh == null or not str(mi.name).to_lower().begins_with("roof"):
			continue
		var xf := to_oval * mi.global_transform
		for si in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(si)
			var mn := m.resource_name.to_lower() if m != null else ""
			if not (mn.contains("soffit") or mn.contains("fascia")):
				continue
			var verts: PackedVector3Array = mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]
			for v in verts:
				var p := xf * v
				if p.y < 15.0:
					continue
				var r := Vector2(p.x / f.x, p.z / f.y).length()
				var k := int(fposmod(atan2(p.z / f.y, p.x / f.x), TAU) / TAU * BUCKETS) % BUCKETS
				if best[k] == null or r < best[k][0] or (absf(r - best[k][0]) < 0.01 and p.y < best[k][1].y):
					best[k] = [r, p]
	var pts := PackedVector3Array()
	var last := Vector3(INF, INF, INF)
	for k in BUCKETS:
		if best[k] == null:
			continue
		var p: Vector3 = best[k][1]
		if p.distance_to(last) < DOT_EVERY:
			continue
		pts.append(p - Vector3(0.0, 1.2, 0.0) - Vector3(p.x, 0.0, p.z).normalized() * 1.5)
		last = p
	if pts.size() < 12:
		return null
	var q := QuadMesh.new()
	q.size = Vector2(DOT_SIZE, DOT_SIZE)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = q
	mm.instance_count = pts.size()
	for i in pts.size():
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, pts[i]))
	var mmi := MultiMeshInstance3D.new()
	mmi.name = "RoofLights"
	mmi.multimesh = mm
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://scripts/ui/match/oval3d_glow.gdshader")
	mat.render_priority = GLOW_PRIORITY
	mat.set_shader_parameter("halo_amount", 0.35)
	mat.set_shader_parameter("core", 0.4)
	mat.set_shader_parameter("brightness", 2.4)
	mmi.material_override = mat
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi
