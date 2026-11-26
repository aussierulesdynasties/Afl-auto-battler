class_name Oval3DBannerCloth
extends RefCounted
## The run-through banner's crepe paper as cloth (Oval3DBanner): a grid of points joined by
## links, hung from the rope along its top and held at the poles and by the squad at its bottom
## corners. The runners push it ahead of them; a link stretched past its limit near a man tears,
## so the paper bulges, rips along a ragged line where the first man hits it, and the flaps sag,
## swing and drape from the rope and the poles while loose sheets drift down onto the grass.
## Positions are in the banner's own frame (x along the paper, y up, z toward the ground side).
## Looks only. Drawn as one cell per instance of a MultiMesh (draw()).

const NX := 48                 # cells across (0.375 m)
const NY := 18                 # cells down (0.36 m)
const SUBSTEPS := 2            # per frame (Graphics: Low, 1)
const ITERATIONS := 4
const DAMP := 0.955            # per 1/60 s: crepe is all drag (about 4 m/s falling at most)
const GRAVITY := Vector3(0.0, -9.8, 0.0)
## A link tears stretched past this (each its own, between the two: a ragged line); far from
## any man, only past TEAR_FREE (the paper's own weight never pulls it apart).
const TEAR := Vector2(1.14, 1.34)
const TEAR_FREE := 2.2
const NEAR := 1.6              # m: a man this near a link can tear it
## A runner, to the paper: a post this wide from the grass to his head, his chest ahead of it.
const BODY_R := 0.5
const BODY_TOP := 2.05

var w := 18.0
var low := 0.5
var top := 7.0
var p := PackedVector3Array()   # points, (NX + 1) a row, rows from the bottom
var q := PackedVector3Array()   # last step's points (Verlet)
var pinned := PackedByteArray()
var h_rest := 0.0
var v_rest := 0.0
var h_cut := PackedByteArray()  # link (i, j)-(i + 1, j): j * NX + i
var v_cut := PackedByteArray()  # link (i, j)-(i, j + 1): j * (NX + 1) + i
var h_tear := PackedFloat32Array()
var v_tear := PackedFloat32Array()
var substeps := SUBSTEPS
var torn := 0                   # links torn so far
## The rips running through the paper: [{x (a cell column), j (row reached), to (last row),
## at (s: when it starts), rate (rows a second), across ([column from, to, row]: then along
## a row under the rope)}].
var rips: Array = []
var _t := 0.0
var _rng := RandomNumberGenerator.new()
var _buf := PackedFloat32Array()


func _init(p_w: float, p_low: float, p_top: float, held_from: float, seed: int) -> void:
	w = p_w
	low = p_low
	top = p_top
	h_rest = w / NX
	v_rest = (top - low) / NY
	var rng := _rng
	rng.seed = seed
	for j in range(NY + 1):
		for i in range(NX + 1):
			var at := Vector3(-w * 0.5 + i * h_rest, low + j * v_rest, 0.0)
			p.append(at)
			q.append(at)
			# The rope along the top, the poles at each end, the squad at the bottom corners.
			var pin := j == NY or i == 0 or i == NX or (j == 0 and absf(at.x) >= held_from)
			pinned.append(1 if pin else 0)
	h_cut.resize(NX * (NY + 1))
	v_cut.resize((NX + 1) * NY)
	h_cut.fill(0)
	v_cut.fill(0)
	for k in range(h_cut.size()):
		h_tear.append(rng.randf_range(TEAR.x, TEAR.y))
	for k in range(v_cut.size()):
		v_tear.append(rng.randf_range(TEAR.x, TEAR.y))
	_buf.resize(NX * NY * 16)


## A man hits the paper at x (banner frame) at time `at`: a tear runs up from his feet, a
## crooked line, to `share` of the way to the rope. The first man's (`split`) runs on up and then
## along under the rope both ways, so the middle of the sheet comes away and falls over them.
func rip(x: float, at: float, share: float, split := false) -> void:
	var i := clampi(int((x + w * 0.5) / h_rest), 2, NX - 3)
	var to := clampi(int(share * NY), 2, NY - 2)
	var r := {"i": i, "j": 0, "to": to, "at": at, "rate": _rng.randf_range(26.0, 34.0), "across": []}
	if split:
		r["to"] = NY - 2
		var reach := int(_rng.randf_range(1.6, 2.8) / h_rest)
		r["across"] = [maxi(1, i - reach), mini(NX - 2, i + reach + int(_rng.randf_range(0.0, 1.2) / h_rest))]
	rips.append(r)


func _run_rips(t: float) -> void:
	for r in rips:
		if t < float(r["at"]):
			continue
		var want := int((t - float(r["at"])) * float(r["rate"]))
		var j := int(r["j"])
		var i := int(r["i"])
		while j < mini(want, int(r["to"]) + 1):
			# Up one row: the link across the line at this row goes; the line wanders a cell.
			_cut_h(i, j)
			if _rng.randf() < 0.35:
				i = clampi(i + (1 if _rng.randf() < 0.5 else -1), 2, NX - 3)
				_cut_h(i, j)
			j += 1
		r["j"] = j
		r["i"] = i
		var across: Array = r["across"]
		if across.size() == 2 and j > int(r["to"]):
			# Then along under the rope, both ways at once, as fast as it ran up.
			var row := int(r["to"])
			var gone := want - int(r["to"]) - 1
			for k in range(1, gone + 1):
				for i2 in [i - k, i + k]:
					if i2 >= int(across[0]) and i2 <= int(across[1]):
						_cut_v(i2, row + (1 if (i2 * 7) % 5 == 0 else 0))


func _cut_h(i: int, j: int) -> void:
	var e := j * NX + i
	if h_cut[e] == 0:
		h_cut[e] = 1
		torn += 1


func _cut_v(i: int, j: int) -> void:
	if j < 0 or j >= NY:
		return
	var e := j * (NX + 1) + i
	if v_cut[e] == 0:
		v_cut[e] = 1
		torn += 1


func idx(i: int, j: int) -> int:
	return j * (NX + 1) + i


## One frame: dt seconds, the men near the paper as [[chest (banner frame), heading]], time t
## (the breeze).
func step(dt: float, men: Array, t: float) -> void:
	var n := maxi(1, substeps)
	var h := dt / n
	if h <= 0.0:
		return
	_run_rips(t)
	for s in range(n):
		_integrate(h, t + s * h)
		for it in range(ITERATIONS):
			_push(men)
			_links(men)


func _integrate(h: float, t: float) -> void:
	var damp := pow(DAMP, h * 60.0)
	var g := GRAVITY * h * h
	for k in range(p.size()):
		if pinned[k] == 1:
			continue
		var at := p[k]
		var v := (at - q[k]) * damp
		q[k] = at
		# A light breeze off the ground, gusting along the paper.
		var wind := Vector3(0.0, 0.0, 0.35 * sin(t * 1.3 + at.x * 0.35) + 0.15 * sin(t * 3.1 - at.x * 0.9))
		at += v + g + wind * h * h
		if at.y < 0.03:
			# The grass: it lies where it lands, dragging.
			at.y = 0.03
			q[k] = Vector3(lerpf(q[k].x, at.x, 0.6), at.y, lerpf(q[k].z, at.z, 0.6))
		p[k] = at


## Each man carries the paper ahead of him until it tears, and shoulders the torn edges aside.
func _push(men: Array) -> void:
	for m in men:
		var c: Vector3 = m[0]
		for k in range(p.size()):
			if pinned[k] == 1:
				continue
			var at := p[k]
			if at.y > BODY_TOP:
				continue
			var dx := at.x - c.x
			var dz := at.z - c.z
			if absf(dx) > BODY_R or dz > BODY_R or dz < -0.9:
				continue
			var d := Vector2(dx, maxf(dz, 0.0))
			var len := d.length()
			if len >= BODY_R:
				continue
			# Out to his edge: ahead of his chest, or off his shoulder to the side.
			var out := d / len if len > 0.05 else Vector2(0.0, 1.0)
			if dz < 0.0:
				out = Vector2(signf(dx) if absf(dx) > 0.01 else 1.0, 0.0)
			at.x = c.x + out.x * BODY_R
			at.z = c.z + out.y * BODY_R
			p[k] = at


func _near(men: Array, a: Vector3) -> bool:
	for m in men:
		var c: Vector3 = m[0]
		if absf(a.x - c.x) < NEAR and absf(a.z - c.z) < NEAR + 1.0:
			return true
	return false


func _links(men: Array) -> void:
	var nx1 := NX + 1
	for j in range(NY + 1):
		for i in range(NX):
			var e := j * NX + i
			if h_cut[e] == 1:
				continue
			_solve(j * nx1 + i, j * nx1 + i + 1, h_rest, e, true, men)
	for j in range(NY):
		for i in range(nx1):
			var e := j * nx1 + i
			if v_cut[e] == 1:
				continue
			_solve(j * nx1 + i, (j + 1) * nx1 + i, v_rest, e, false, men)


func _solve(a: int, b: int, rest: float, e: int, across: bool, men: Array) -> void:
	var pa := p[a]
	var pb := p[b]
	var d := pb - pa
	var len := d.length()
	if len < 1e-6:
		return
	var stretch := len / rest
	var limit: float = h_tear[e] if across else v_tear[e]
	if stretch > TEAR_FREE or (stretch > limit and _near(men, pa)):
		if across:
			h_cut[e] = 1
		else:
			v_cut[e] = 1
		torn += 1
		return
	var wa := 0.0 if pinned[a] == 1 else 1.0
	var wb := 0.0 if pinned[b] == 1 else 1.0
	if wa + wb == 0.0:
		return
	var fix := d * ((len - rest) / len / (wa + wb))
	p[a] = pa + fix * wa
	p[b] = pb - fix * wb


func _cell_whole(i: int, j: int) -> bool:
	return h_cut[j * NX + i] == 0 and h_cut[(j + 1) * NX + i] == 0 \
			and v_cut[j * (NX + 1) + i] == 0 and v_cut[j * (NX + 1) + i + 1] == 0


## How many cells are torn out (a line of tear, or loose).
func cells_torn() -> int:
	var n := 0
	for j in range(NY):
		for i in range(NX):
			if not _cell_whole(i, j):
				n += 1
	return n


## The cells into mm (TRANSFORM_3D with custom data; QuadMesh 1 x 1): each cell's quad laid
## between its four points, a torn-out cell gone, and its torn neighbours' edges ragged
## (oval3d_banner.gdshader: 1 left, 2 right, 4 bottom, 8 top, 16 on the grass).
func draw(mm: MultiMesh) -> void:
	var nx1 := NX + 1
	var o := 0
	for j in range(NY):
		for i in range(NX):
			var whole := _cell_whole(i, j)
			var u0 := float(i) / NX
			var v0 := float(NY - 1 - j) / NY
			if not whole:
				for z in range(12):
					_buf[o + z] = 0.0
				_buf[o + 12] = u0
				_buf[o + 13] = v0
				_buf[o + 14] = 0.0
				_buf[o + 15] = 0.0
				o += 16
				continue
			var a := p[j * nx1 + i]
			var b := p[j * nx1 + i + 1]
			var c := p[(j + 1) * nx1 + i]
			var d := p[(j + 1) * nx1 + i + 1]
			var x := ((b - a) + (d - c)) * 0.5
			var y := ((c - a) + (d - b)) * 0.5
			var nz := x.cross(y)
			nz = nz.normalized() * 0.01 if nz.length() > 1e-6 else Vector3(0, 0, 0.01)
			var org := (a + b + c + d) * 0.25
			var mask := 0
			if i > 0 and not _cell_whole(i - 1, j):
				mask |= 1
			if i < NX - 1 and not _cell_whole(i + 1, j):
				mask |= 2
			if j > 0 and not _cell_whole(i, j - 1):
				mask |= 4
			if j < NY - 1 and not _cell_whole(i, j + 1):
				mask |= 8
			if maxf(maxf(a.y, b.y), maxf(c.y, d.y)) < 0.1:
				mask |= 16
			_buf[o] = x.x
			_buf[o + 1] = y.x
			_buf[o + 2] = nz.x
			_buf[o + 3] = org.x
			_buf[o + 4] = x.y
			_buf[o + 5] = y.y
			_buf[o + 6] = nz.y
			_buf[o + 7] = org.y
			_buf[o + 8] = x.z
			_buf[o + 9] = y.z
			_buf[o + 10] = nz.z
			_buf[o + 11] = org.z
			_buf[o + 12] = u0
			_buf[o + 13] = v0
			_buf[o + 14] = 0.0
			_buf[o + 15] = float(mask)
			o += 16
	mm.buffer = _buf
