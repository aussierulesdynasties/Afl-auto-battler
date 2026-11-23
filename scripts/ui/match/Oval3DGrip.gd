class_name Oval3DGrip
extends SkeletonModifier3D
## A hand closed round something held (row 202: a trainer's drink bottle). Each frame, after
## the clip has posed him, the four fingers curl round the bottle's barrel and the thumb closes
## over it, so the bottle sits in a gripped fist instead of passing through an open hand.
##
## The curl is worked out from the skeleton's rest, not from fixed bone axes, so it fits any
## body with the UE hand bones (hand_r, index_01_r ... thumb_03_r).

## How far each knuckle bends (degrees): base, middle, tip. Round a 7.5 cm bottle.
const CURL := [62.0, 72.0, 40.0]
const THUMB := [34.0, 48.0, 40.0]
const FINGERS := ["index", "middle", "ring", "pinky"]

var side := "r"
var _hand := -1
## In the hand's own frame: across the knuckles (little finger to index), along the fingers,
## and out of the palm.
var _across := Vector3.ZERO
var _along := Vector3.ZERO
var _palm := Vector3.ZERO
var _thumb_axis := Vector3.ZERO
var _chains := []
var _thumb := []
var _held := Vector3.ZERO     # the bottle's middle, in the hand's frame


## The place, in the hand bone's frame, where a bottle (its barrel along +Y, origin at its
## middle) sits in this grip: across the palm, cap out past the index finger.
func held_at(skel: Skeleton3D) -> Transform3D:
	_setup(skel)
	if _hand < 0:
		return Transform3D.IDENTITY
	var at := _held
	var y := _across
	var z := _palm.cross(y).normalized()
	var x := y.cross(z).normalized()
	return Transform3D(Basis(x, y, z), at)


func _setup(skel: Skeleton3D) -> void:
	if _hand >= 0 or skel == null:
		return
	_hand = skel.find_bone("hand_" + side)
	if _hand < 0:
		return
	var hg := skel.get_bone_global_rest(_hand)
	var inv := hg.affine_inverse()
	var p := func(n: String) -> Vector3:
		return inv * skel.get_bone_global_rest(skel.find_bone(n + "_" + side)).origin
	_across = (p.call("index_01") - p.call("pinky_01")).normalized()
	_along = (p.call("middle_02") - p.call("middle_01")).normalized()
	# Out of the palm: the thumb sits on the palm side of the line of the knuckles.
	var n := _across.cross(_along).normalized()
	var t: Vector3 = p.call("thumb_02") - p.call("middle_01")
	_palm = n if t.dot(n) > 0.0 else -n
	# The fingers curl about the knuckle line.
	for f in FINGERS:
		var c := []
		for j in range(3):
			c.append(skel.find_bone("%s_%02d_%s" % [f, j + 1, side]))
		_chains.append(c)
	for j in range(3):
		_thumb.append(skel.find_bone("thumb_%02d_%s" % [j + 1, side]))
	# The barrel runs across the hand under the first finger bones, one bottle radius out
	# of the palm.
	var k1: Vector3 = p.call("middle_01")
	_held = k1.lerp(p.call("middle_02"), 0.35) + _palm * 0.042
	# The thumb wraps round the barrel, so it bends about the barrel's line (across the hand).
	_thumb_axis = _across


func _process_modification() -> void:
	var skel := get_skeleton()
	_setup(skel)
	if _hand < 0:
		return
	var hg := skel.get_bone_global_pose(_hand)
	for c in _chains:
		_curl(skel, hg, c, _across, CURL)
	_curl(skel, hg, _thumb, _thumb_axis, THUMB)


## Bends the bones of chain (parent first) about axis (hand frame) by angles, each its tip
## toward the bottle's barrel, and writes their local poses.
func _curl(skel: Skeleton3D, hg: Transform3D, chain: Array, axis_h: Vector3, angles: Array) -> void:
	if chain.has(-1):
		return
	var axis := (hg.basis * axis_h).normalized()
	var mid := hg * _held
	# The barrel's line through its middle: what the fingers wrap round.
	var line := (hg.basis * _across).normalized()
	var parent := skel.get_bone_global_pose(skel.get_bone_parent(chain[0]))
	for j in range(chain.size()):
		var b: int = chain[j]
		var g := parent * skel.get_bone_pose(b)
		var tip := g.basis.y.normalized() * 0.03
		var a := deg_to_rad(float(angles[j]) * influence)
		if _off_line(g.origin + tip.rotated(axis, a), mid, line) > _off_line(g.origin + tip.rotated(axis, -a), mid, line):
			a = -a
		g.basis = Basis(axis, a) * g.basis
		skel.set_bone_pose_rotation(b, (parent.basis.inverse() * g.basis).get_rotation_quaternion())
		parent = g


## How far point q is from the barrel's line.
static func _off_line(q: Vector3, mid: Vector3, line: Vector3) -> float:
	var d := q - mid
	return (d - line * d.dot(line)).length()
