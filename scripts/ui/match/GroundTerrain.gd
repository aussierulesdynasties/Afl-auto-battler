class_name GroundTerrain
extends RefCounted
## The real land round a ground, from tools/grounds/terrain (bare-earth LiDAR: Geoscience
## Australia 5 m on the mainland, the LIST 2 m in Tasmania, LINZ 1 m in Wellington). The file is
## `terrain.bin` in the ground's asset folder: eight float32 (a fine grid's half width m, step m and
## cells a side, then a coarse grid's, then two zeros), then each grid as int16 centimetres above the
## turf at the centre circle, rows south to north, columns west to east. `height(x, z)` takes the
## model's own metres (x east, z south) and gives the land's y in the model, the arena floor (FIT)
## being the turf.

var fine: Array = []    # [half, step, cells, bytes]
var coarse: Array = []
## The centre circle in the model's metres, and the model's y there (its arena floor).
var cx := 0.0
var cz := 0.0
var floor_y := 0.0


static func load_for(dir: String, fit: Array) -> GroundTerrain:
	var path := dir + "terrain.bin"
	if not FileAccess.file_exists(path):
		return null
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.size() < 32:
		return null
	var head := bytes.slice(0, 32).to_float32_array()
	var nf := int(head[2])
	var nc := int(head[5])
	if bytes.size() != 32 + 2 * (nf * nf + nc * nc):
		push_warning("terrain.bin in %s has the wrong size" % dir)
		return null
	var t := GroundTerrain.new()
	t.fine = [head[0], head[1], nf, bytes.slice(32, 32 + 2 * nf * nf)]
	t.coarse = [head[3], head[4], nc, bytes.slice(32 + 2 * nf * nf)]
	if fit.size() >= 3:
		t.cx = float(fit[0])
		t.cz = float(fit[1])
		t.floor_y = float(fit[2])
	return t


## The land's y at the model's (x, z), bilinear between cells: the fine grid near the ground, the
## coarse one past it, and the coarse grid's edge beyond that.
func height(x: float, z: float) -> float:
	var e := x - cx
	var nn := -(z - cz)
	var g: Array = fine if maxf(absf(e), absf(nn)) < float(fine[0]) - float(fine[1]) else coarse
	return floor_y + 0.01 * _sample(g, e, nn)


static func _sample(g: Array, e: float, nn: float) -> float:
	var half: float = g[0]
	var step: float = g[1]
	var n: int = g[2]
	var h: PackedByteArray = g[3]
	var px := clampf((e + half) / step, 0.0, n - 1.001)
	var py := clampf((nn + half) / step, 0.0, n - 1.001)
	var i := int(px)
	var j := int(py)
	var fx := px - i
	var fy := py - j
	var a := h.decode_s16((j * n + i) * 2)
	var b := h.decode_s16((j * n + i + 1) * 2)
	var c := h.decode_s16(((j + 1) * n + i) * 2)
	var d := h.decode_s16(((j + 1) * n + i + 1) * 2)
	return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


## The lowest land under a footprint (model x, z): a building's ground floor, so no wall hangs in
## the air on the low side.
func base(foot: PackedVector2Array) -> float:
	var lo := INF
	var mid := Vector2.ZERO
	for p in foot:
		lo = minf(lo, height(p.x, p.y))
		mid += p
	if foot.size() > 0:
		lo = minf(lo, height(mid.x / foot.size(), mid.y / foot.size()))
	return lo
