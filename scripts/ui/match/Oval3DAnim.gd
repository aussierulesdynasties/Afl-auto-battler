class_name Oval3DAnim
extends RefCounted
## The 3D oval's animation controller (row 198, owned by the animation session; Oval3D.gd only
## calls frame(), step() and event()). Picks each player's clip, facing and rate from his token
## and the ball, and advances his AnimationPlayer by dt: jog / idle / carry, and the two-man
## tackle clips (row 197).

const JOG_SPEED := 6.0
const RUN_FROM := 1.4          # m/s: slower than this he stands
## Eyes on the ball (plan §2.6): the neck takes part of the turn and the head the rest, inside a
## real person's range (about 80 degrees each way, 35 up or down), so nobody turns like an owl.
## The carrier looks where he runs, not at the ball in his hands.
const LOOK := [["neck_01", 35.0, 20.0, 0.5], ["head", 45.0, 25.0, 1.0]]  # bone, yaw, pitch, influence
const LOOK_FOLLOW := 8.0       # 1/s: how fast the eyes catch a moving ball
const BALL_R := 0.09          # m: the ball on the turf (Oval3D.BALL_R)

## Tackles (row 197). Each pair is one motion-capture take of two men, tackler and tacklee,
## sharing an origin, a clock and a length (tackle_pairs.json: contact_s is where the arms
## meet). Both men join the take at the point of its run-in where its tackler is as far from
## its tacklee as ours is (at least LEAD before the contact), the tacklee anchored where he
## stands, the take turned about him so its tackler comes from where ours is.
const PAIRS := "res://assets/oval3d/tackle_pairs.json"
const LEAD := 0.3              # clip s: the run-in starts at least this long before the contact
const LEAD_MIN := 0.12         # the least run-in, when the tackle comes without warning
const LEAD_RATE := 1.5         # fastest the run-in plays to fit a short warning
const SLOW := 0.6              # slowest it plays while the contact is still to come
const CATCH_UP := 2.0          # fastest it plays when the contact has come first
const HURRY := 2.0             # how fast the get-up plays once the play has moved on
const FAR := 5.0               # m: his token this far from him = the play has moved on
const BLEND := 0.2             # s: the pose he was in eases into the clip (and the clip out)
const GAP_CLOSE := 4.0         # m/s: after a tackle he runs back to his spot, at least this fast
const GAP_MAX := 9.0           # m/s: and at most this fast
const REACH := 1.6             # m: MatchDirector's chase ends this close (its "chase" phase)
const STEP := 1.0 / 30.0       # s: the takes' frame

var director: MatchDirector
var players: Array
## One record per tackle drawn: who, victim, pair, start_t, event_t, hit_t (the clock when the
## clip's arms meet), lead (clip s of run-in), turn_deg (the tacklee's turn to face it),
## warp_m / warp_deg (the tackler's correction over the run-in), at (the director's tackle
## spot), contact (where the clip's arms meet), root (the tacklee's hips then). For the
## capture tool and the tests.
var tackles: Array = []
var _targets: Array = []       # per player: the Node3D his look-at modifiers aim at
var _looks: Array = []         # per player: his LookAtModifier3D nodes
var _pairs := {}               # take name -> its tackle_pairs.json entry
var _clock := 0.0              # s of animation time
var _rig := Transform3D()      # a figure's node -> its skeleton
var _pelvis := -1
var _hips := {}                # animation name -> [pelvis position track, rotation track]
var _in: Array = []            # per player: the pair he is in, {} for none
var _blend: Array = []         # per player: the pose he is easing out of, {} for none
var _back: Array = []          # per player: where a finished pair left him (INF: nowhere)
var _gap: Array = []           # per player: his drawn spot minus his token's, closing
var _rate: Array = []          # per player: the rate his running clip played at last
var _takes := {}               # take name -> {dist: hips apart, foot: planted foot} per STEP
var _tracks := {}              # animation name -> {bone: rotation track}, "hips": position track


func _init(p_director: MatchDirector, p_players: Array) -> void:
	director = p_director
	players = p_players
	for p in players:
		_add_look(p)
		_in.append({})
		_blend.append({})
		_back.append(Vector2.INF)
		_gap.append(Vector2.ZERO)
		_rate.append(1.0)
	var res = load(PAIRS)
	if res is JSON:
		_pairs = (res as JSON).data
	if players.size() > 0:
		var p: Dictionary = players[0]
		var skel: Skeleton3D = p["skel"]
		_pelvis = skel.find_bone("pelvis")
		var n: Node = skel
		while n != null and n != p["node"]:
			_rig = (n as Node3D).transform * _rig
			n = n.get_parent()
		_read_takes(p)


## Each take's run-in, frame by frame: how far apart the two men's hips are and which of the
## tackler's feet is on the ground (read once, on the first figure, before the match draws).
func _read_takes(p: Dictionary) -> void:
	var ap: AnimationPlayer = p["anim"]
	for name in _pairs:
		var cs := float(_pairs[name]["contact_s"])
		var dist := []
		var foot := []
		var k := 0
		while k * STEP <= cs + 0.001:
			var hk := _clip_hips(ap, name + "_tackler", k * STEP).origin
			var he := _clip_hips(ap, name + "_tacklee", k * STEP).origin
			dist.append(Vector2(hk.x - he.x, hk.z - he.z).length())
			ap.play(name + "_tackler")
			ap.seek(k * STEP, true)
			foot.append(_planted(p))
			k += 1
		_takes[name] = {"dist": dist, "foot": foot}
	ap.play("idle")


## 0 when his left foot is the lower, 1 when his right is.
func _planted(p: Dictionary) -> int:
	var skel: Skeleton3D = p["skel"]
	var l := (_rig * skel.get_bone_global_pose(skel.find_bone("ball_l"))).origin.y
	var r := (_rig * skel.get_bone_global_pose(skel.find_bone("ball_r"))).origin.y
	return 0 if l < r else 1


## Clip seconds of a take's run-in from where its tackler is `d` metres from its tacklee to the
## contact (the whole run-in when ours is farther out than the take starts).
func _lead(name: String, d: float) -> float:
	var cs := float(_pairs[name]["contact_s"])
	var dist: Array = _takes[name]["dist"]
	for k in range(dist.size()):
		if float(dist[k]) <= d:
			return clampf(cs - k * STEP, LEAD_MIN, cs)
	return LEAD_MIN


## Where his hips are drawn, on the ground.
func _drawn(i: int) -> Vector2:
	var h := _hips_world(players[i])
	return Vector2(h.origin.x, h.origin.z)


func _add_look(p: Dictionary) -> void:
	var skel: Skeleton3D = p["skel"]
	var target := Node3D.new()
	(p["node"] as Node3D).add_child(target)
	target.top_level = true
	var mods := []
	for l in LOOK:
		var m := LookAtModifier3D.new()
		m.bone_name = l[0]
		m.forward_axis = SkeletonModifier3D.BONE_AXIS_PLUS_Z
		m.primary_rotation_axis = Vector3.AXIS_Y
		m.use_angle_limitation = true
		m.symmetry_limitation = true
		m.primary_limit_angle = deg_to_rad(l[1] * 2.0)
		m.secondary_limit_angle = deg_to_rad(l[2] * 2.0)
		m.influence = l[3]
		skel.add_child(m)
		m.target_node = m.get_path_to(target)
		mods.append(m)
	_targets.append(target)
	_looks.append(mods)


## Once a frame, before the contacts and the players: the clock, a tackle about to land (its
## clip starts now), and every running pair's clip time.
func frame(dt: float) -> void:
	_clock += dt
	var ahead := director.tackle_ahead()
	if not ahead.is_empty() and not _pairs.is_empty():
		var who := int(ahead["who"])
		var v := int(ahead["victim"])
		var pr: Dictionary = _in[who]
		if pr.is_empty() or int(pr["who"]) != who or int(pr["victim"]) != v:
			var due := _due(who, v, float(ahead["left"]))
			# Start as soon as the run-in of some take, from the distance he is out, fits.
			var need := LEAD
			var d := _drawn(who).distance_to(_drawn(v))
			for name in _pairs:
				need = maxf(need, _lead(name, d))
			if due <= need:
				_start(who, v, due, false)
	var seen := {}
	for pr in _in:
		if pr.is_empty() or seen.has(pr["id"]):
			continue
		seen[pr["id"]] = true
		_advance(pr, dt)


## Animation seconds until the chase from `who` to `v` reaches MatchDirector's REACH.
func _due(who: int, v: int, left: float) -> float:
	var a: Dictionary = director.tokens[who]
	var b: Dictionary = director.tokens[v]
	var gap: Vector2 = (b["pos"] as Vector2) - (a["pos"] as Vector2)
	var d := gap.length()
	if d < 0.001:
		return 0.0
	var closing := ((a["vel"] as Vector2) - (b["vel"] as Vector2)).dot(gap / d) * MatchDirector.TEMPO
	return minf(maxf(0.0, d - REACH) / maxf(closing, 1.0), left / MatchDirector.TEMPO)


func _advance(pr: Dictionary, dt: float) -> void:
	if pr["fresh"]:
		pr["fresh"] = false
		return
	var cs := float(pr["cs"])
	var c := float(pr["c"])
	var rate := 1.0
	if c < cs:
		if pr["arrived"]:
			rate = CATCH_UP
		else:
			var ahead := director.tackle_ahead()
			var due := 0.05
			if not ahead.is_empty() and int(ahead["who"]) == int(pr["who"]):
				due = _due(int(pr["who"]), int(pr["victim"]), float(ahead["left"]))
			rate = clampf((cs - c) / maxf(due, 0.05), SLOW, LEAD_RATE)
	else:
		# Down: the get-up hurries when the play has gone on without them.
		for i in [int(pr["who"]), int(pr["victim"])]:
			if _in[i] == pr and _drawn(i).distance_to(director.tokens[i]["pos"]) > FAR:
				rate = HURRY
	var nc := c + dt * rate
	if c < cs and nc >= cs:
		_hit(pr)
	pr["c"] = nc


## The arms meet in the clip: where, and when, against the director's tackle.
func _hit(pr: Dictionary) -> void:
	var rec: Dictionary = pr["rec"]
	rec["hit_t"] = _clock
	var e: Dictionary = _pairs[pr["name"]]
	var cp: Transform3D = pr["P"]
	var at := cp * Vector3(float(e["contact"]["x"]), 0.0, float(e["contact"]["z"]))
	rec["contact"] = Vector2(at.x, at.z)
	var v := int(pr["victim"])
	var hips := _hips_world(players[v])
	rec["root"] = Vector2(hips.origin.x, hips.origin.z)


## Start a pair: the take whose tackler comes from nearest where ours is, turned about the
## tacklee. `due` is the animation seconds before the director's contact; `arrived` when it
## has already come.
func _start(who: int, v: int, due: float, arrived: bool, at := Vector2.INF) -> void:
	for i in [who, v]:
		if not (_in[i] as Dictionary).is_empty():
			_leave(i)
	var pk: Dictionary = players[who]
	var pv: Dictionary = players[v]
	var far := false
	for i in [who, v]:
		var tok: Vector2 = director.tokens[i]["pos"]
		if _drawn(i).distance_to(tok) > FAR:
			# Still on his way back from an earlier tackle, long after the play moved on: he
			# joins this one from where the director has him.
			(players[i]["node"] as Node3D).position = Vector3(tok.x, 0.0, tok.y)
			_gap[i] = Vector2.ZERO
			_back[i] = Vector2.INF
			far = true
	var hk := _hips_world(pk)
	var hv := _hips_world(pv)
	var K := Vector2(hk.origin.x, hk.origin.z)
	var V := Vector2(hv.origin.x, hv.origin.z)
	var yk := _yaw_of(hk.basis)
	var yv := _yaw_of(hv.basis)
	var ap: AnimationPlayer = pk["anim"]
	var running := ap.current_animation in ["jog", "carry"]
	var foot := _planted(pk)
	var best := {}
	for name in _pairs:
		var e: Dictionary = _pairs[name]
		var cs := float(e["contact_s"])
		# Join the take where its tackler is as far out as ours.
		var lead := _lead(name, (K - V).length())
		if arrived:
			lead = minf(lead, LEAD_MIN)
		var c0 := cs - lead
		var ce := _clip_hips(ap, name + "_tacklee", c0)
		var ck := _clip_hips(ap, name + "_tackler", c0)
		var e2 := Vector2(ce.origin.x, ce.origin.z)
		var k2 := Vector2(ck.origin.x, ck.origin.z)
		var theta := yv - _yaw_of(ce.basis)
		if (K - V).length() > 0.3:
			theta = _yaw_vec(K - V) - _yaw_vec(k2 - e2)
		var turn := wrapf(yv - (theta + _yaw_of(ce.basis)), -PI, PI)
		var score := absf(turn) + 0.1 * absf((K - V).length() - (k2 - e2).length())
		# The take whose tackler has the same foot down as ours runs on in step.
		var feet: Array = _takes[name]["foot"]
		if running and int(feet[clampi(roundi(c0 / STEP), 0, feet.size() - 1)]) != foot:
			score += 0.35
		if best.is_empty() or score < float(best["score"]):
			best = {"name": name, "theta": theta, "turn": turn, "ce": ce, "ck": ck, "c0": c0,
					"cs": cs, "score": score}
	if best.is_empty():
		return
	var name: String = best["name"]
	var P := Transform3D(Basis(Vector3.UP, float(best["theta"])), Vector3.ZERO)
	var ce: Transform3D = best["ce"]
	var ck: Transform3D = best["ck"]
	P.origin = Vector3(V.x, 0.0, V.y) - P.basis * Vector3(ce.origin.x, 0.0, ce.origin.z)
	var pk3 := P * Vector3(ck.origin.x, 0.0, ck.origin.z)
	var wk := Vector3(K.x, 0.0, K.y) - pk3
	var dyk := wrapf(yk - (float(best["theta"]) + _yaw_of(ck.basis)), -PI, PI)
	var rec := {"who": who, "victim": v, "pair": name, "start_t": _clock, "event_t": -1.0,
			"hit_t": -1.0, "lead": float(best["cs"]) - float(best["c0"]),
			"turn_deg": rad_to_deg(float(best["turn"])), "warp_m": wk.length(),
			"warp_deg": rad_to_deg(dyk), "at": at, "contact": Vector2.INF, "root": Vector2.INF,
			"from": K, "stand": V, "far": far}
	if arrived:
		rec["event_t"] = _clock
	tackles.append(rec)
	var pr := {"id": tackles.size(), "name": name, "who": who, "victim": v, "P": P,
			"c0": float(best["c0"]), "c": float(best["c0"]), "cs": float(best["cs"]),
			"len": float(_pairs[name]["length_s"]), "arrived": arrived, "rec": rec,
			# Started by frame() this frame: its clock has already been stepped past.
			"fresh": not arrived,
			"roles": {
				who: {"anim": name + "_tackler", "pivot": pk3, "w": wk, "dy": dyk},
				v: {"anim": name + "_tacklee", "pivot": Vector3(V.x, 0.0, V.y), "w": Vector3.ZERO,
						"dy": float(best["turn"])}}}
	for i in [who, v]:
		_snap(i, players[i])
		_in[i] = pr
		_back[i] = Vector2.INF
		_gap[i] = Vector2.ZERO
		for m in _looks[i]:
			(m as LookAtModifier3D).active = false


## Pose player i for this frame. holder = the index with the ball in his hands, or -1.
func step(i: int, p: Dictionary, holder: int, pos: Vector2, vel: Vector2, dt: float) -> void:
	if not (_in[i] as Dictionary).is_empty():
		_step_pair(i, p, dt)
		return
	var node: Node3D = p["node"]
	if _back[i] != Vector2.INF:
		_gap[i] = (_back[i] as Vector2) - pos
		_back[i] = Vector2.INF
	var gap: Vector2 = _gap[i]
	if gap != Vector2.ZERO:
		# Back from a tackle: he runs to his spot.
		var back := clampf(2.0 * gap.length(), GAP_CLOSE, GAP_MAX)
		_gap[i] = gap - gap.limit_length(back * dt)
		if gap.length() > 0.05:
			vel = vel - gap.normalized() * back
		node.position = Vector3(pos.x + (_gap[i] as Vector2).x, 0.0, pos.y + (_gap[i] as Vector2).y)
	var speed := vel.length()
	var ap: AnimationPlayer = p["anim"]
	var want := "carry" if i == holder else "idle"
	var rate := 0.0 if i == holder else 1.0
	if speed > RUN_FROM:
		node.rotation.y = atan2(vel.x, vel.y)
		want = "carry" if i == holder else "jog"
		rate = clampf(speed / JOG_SPEED, 0.45, 2.3)
	elif i != holder:
		# Standing: face the ball (the carrier keeps his heading).
		var to: Vector2 = (director.ball["pos"] as Vector2) - pos
		if to.length() > 0.5:
			node.rotation.y = atan2(to.x, to.y)
	if ap.current_animation != want:
		var at := fmod(float(i) * 0.137, 0.66)
		if ap.current_animation in ["jog", "carry"]:
			at = ap.current_animation_position
		ap.play(want)
		ap.seek(fmod(at, ap.current_animation_length), false)
	if want == "carry" and rate == 0.0:
		# Standing with the ball: the carry's first key, both legs under him (poses.carry
		# at p = 0), not frozen mid-stride.
		ap.seek(0.0, false)
	# A zero step leaves a freshly played pose unapplied (a standing holder kept the idle
	# arms), so a still pose still advances by a sliver.
	ap.advance(maxf(dt * rate, 1e-4))
	_rate[i] = rate
	_ease(i, p, dt)
	_look_at_ball(i, i == holder, dt)


## A man in a pair: the take at the pair's clip time, placed by the pair (and, over the run-in,
## the correction from where he really was), his club ring under his hips.
func _step_pair(i: int, p: Dictionary, dt: float) -> void:
	var pr: Dictionary = _in[i]
	var role: Dictionary = pr["roles"][i]
	var ap: AnimationPlayer = p["anim"]
	var c := minf(float(pr["c"]), float(pr["len"]))
	if ap.current_animation != role["anim"]:
		ap.play(role["anim"])
	ap.seek(c, true)
	var f := 0.0
	if float(pr["cs"]) > float(pr["c0"]):
		f = 1.0 - smoothstep(float(pr["c0"]), float(pr["cs"]), c)
	var pivot: Vector3 = role["pivot"]
	var warp := Transform3D(Basis(Vector3.UP, float(role["dy"]) * f), pivot + (role["w"] as Vector3) * f) \
			* Transform3D(Basis.IDENTITY, -pivot)
	var node: Node3D = p["node"]
	node.transform = warp * (pr["P"] as Transform3D)
	_ease(i, p, dt)
	var hips := _rig * (p["skel"] as Skeleton3D).get_bone_global_pose(_pelvis)
	(p["ring"] as Node3D).position = Vector3(hips.origin.x, 0.03, hips.origin.z)
	if float(pr["c"]) >= float(pr["len"]):
		_leave(i)


## Out of the pair: he stands where the take left him, facing as his hips do, and eases into
## running or standing from there.
func _leave(i: int) -> void:
	var p: Dictionary = players[i]
	var node: Node3D = p["node"]
	var hips := _hips_world(p)
	_snap(i, p)
	node.transform = Transform3D(Basis(Vector3.UP, _yaw_of(hips.basis)), Vector3(hips.origin.x, 0.0, hips.origin.z))
	(p["ring"] as Node3D).position = Vector3(0.0, 0.03, 0.0)
	_back[i] = Vector2(hips.origin.x, hips.origin.z)
	_in[i] = {}


## Hold the pose he is in now, to ease out of over BLEND (_ease).
func _snap(i: int, p: Dictionary) -> void:
	var skel: Skeleton3D = p["skel"]
	var rots := []
	for b in range(skel.get_bone_count()):
		rots.append(skel.get_bone_pose_rotation(b))
	_blend[i] = {"rots": rots, "hips": skel.get_bone_pose_position(_pelvis),
			"yaw": (p["node"] as Node3D).rotation.y, "t": 0.0, "src": ""}
	var ap: AnimationPlayer = p["anim"]
	if (_in[i] as Dictionary).is_empty() and ap.current_animation in ["jog", "carry", "idle"]:
		# Out of running or standing: that clip keeps playing under the ease, so his legs keep
		# stepping as they were instead of a frozen stride dragging along the turf.
		_blend[i]["src"] = ap.current_animation
		_blend[i]["st"] = ap.current_animation_position


## Ease from the held pose into the one the clip just set. The hips keep the clip's place on
## the ground (the node carries that) and their facing in the world, so nobody spins or slides.
func _ease(i: int, p: Dictionary, dt: float) -> void:
	var b: Dictionary = _blend[i]
	if b.is_empty():
		return
	b["t"] = float(b["t"]) + dt
	var w := smoothstep(0.0, BLEND, float(b["t"]))
	if w >= 1.0:
		_blend[i] = {}
		return
	var skel: Skeleton3D = p["skel"]
	var rots: Array = b["rots"]
	var hips_from: Vector3 = b["hips"]
	var src := str(b["src"])
	if src != "":
		var a := (p["anim"] as AnimationPlayer).get_animation(src)
		var tr := _bone_tracks(src, a, skel)
		b["st"] = fmod(float(b["st"]) + dt * float(_rate[i]), maxf(a.length, 0.001))
		rots = rots.duplicate()
		for bone in tr:
			if bone is int:
				rots[bone] = a.rotation_track_interpolate(int(tr[bone]), float(b["st"]))
		if int(tr["hips"]) >= 0:
			hips_from = a.position_track_interpolate(int(tr["hips"]), float(b["st"]))
	for k in range(rots.size()):
		if k != _pelvis:
			skel.set_bone_pose_rotation(k, (rots[k] as Quaternion).slerp(skel.get_bone_pose_rotation(k), w))
	var up := skel.get_bone_parent(_pelvis)
	var to_model := _rig.basis * (skel.get_bone_global_pose(up).basis if up >= 0 else Basis.IDENTITY)
	var turn := Basis(Vector3.UP, float(b["yaw"]) - (p["node"] as Node3D).rotation.y)
	var held := Quaternion((to_model.inverse() * turn * to_model).orthonormalized()) * (rots[_pelvis] as Quaternion)
	skel.set_bone_pose_rotation(_pelvis, held.slerp(skel.get_bone_pose_rotation(_pelvis), w))
	var height := (to_model.inverse() * Vector3.UP).normalized()
	var cur := skel.get_bone_pose_position(_pelvis)
	var h := lerpf(hips_from.dot(height), cur.dot(height), w)
	skel.set_bone_pose_position(_pelvis, cur + height * (h - cur.dot(height)))


## An animation's rotation track per bone index, and its hips' position track ("hips").
func _bone_tracks(name: String, a: Animation, skel: Skeleton3D) -> Dictionary:
	if not _tracks.has(name):
		var tr := {"hips": -1}
		for k in range(a.get_track_count()):
			var bone := skel.find_bone(str(a.track_get_path(k)).get_slice(":", 1))
			if bone < 0:
				continue
			if a.track_get_type(k) == Animation.TYPE_ROTATION_3D:
				tr[bone] = k
			elif a.track_get_type(k) == Animation.TYPE_POSITION_3D and bone == _pelvis:
				tr["hips"] = k
		_tracks[name] = tr
	return _tracks[name]


## A player's hips in Oval3D's space, as drawn now.
func _hips_world(p: Dictionary) -> Transform3D:
	return (p["node"] as Node3D).transform * _rig * (p["skel"] as Skeleton3D).get_bone_global_pose(_pelvis)


## A take's hips at clip time c, in the figure's own space (read off the clip, not played).
func _clip_hips(ap: AnimationPlayer, anim: String, c: float) -> Transform3D:
	if not _hips.has(anim):
		var a := ap.get_animation(anim)
		var tr := [-1, -1]
		for k in range(a.get_track_count()):
			if str(a.track_get_path(k)).ends_with(":pelvis"):
				if a.track_get_type(k) == Animation.TYPE_POSITION_3D:
					tr[0] = k
				elif a.track_get_type(k) == Animation.TYPE_ROTATION_3D:
					tr[1] = k
		_hips[anim] = [a, tr]
	var a: Animation = _hips[anim][0]
	var tr: Array = _hips[anim][1]
	var skel: Skeleton3D = players[0]["skel"]
	var rest := skel.get_bone_rest(_pelvis)
	var pos := a.position_track_interpolate(tr[0], c) if tr[0] >= 0 else rest.origin
	var rot := a.rotation_track_interpolate(tr[1], c) if tr[1] >= 0 else rest.basis.get_rotation_quaternion()
	var up := skel.get_bone_parent(_pelvis)
	var parent := skel.get_bone_global_rest(up) if up >= 0 else Transform3D()
	return _rig * parent * Transform3D(Basis(rot), pos)


## The way a pair of hips faces, as a node yaw (0 faces +Z): from the hip-to-hip axis, which
## stays level whether he runs, bends or lies on his front.
func _yaw_of(b: Basis) -> float:
	var x := b.x
	return atan2(-x.z, x.x)


func _yaw_vec(v: Vector2) -> float:
	return atan2(v.x, v.y)


func _look_at_ball(i: int, carrying: bool, dt: float) -> void:
	var bp: Vector2 = director.ball["pos"]
	var h := float(director.ball.get("h", 0.0))
	var want := Vector3(bp.x, maxf(h, BALL_R), bp.y)
	var target: Node3D = _targets[i]
	if dt <= 0.0 or target.global_position == Vector3.ZERO:
		target.global_position = want
	else:
		target.global_position = target.global_position.lerp(want, clampf(dt * LOOK_FOLLOW, 0.0, 1.0))
	for m in _looks[i]:
		(m as LookAtModifier3D).active = not carrying


## A touch of the ball (or the man) at its moment of contact (Oval3D.anim_event). A tackle
## starts its pair if the run-in has not (the contact came without warning) and marks the
## contact's time; any other touch by a man in a pair takes him out of it.
func event(i: int, kind: StringName, at: Vector2, other := -1) -> void:
	if i < 0 or i >= _in.size():
		return
	if kind == &"tackle" and other >= 0 and other < _in.size() and not _pairs.is_empty():
		var pr: Dictionary = _in[i]
		if pr.is_empty() or int(pr["who"]) != i or int(pr["victim"]) != other:
			_start(i, other, 0.0, true, at)
			return
		pr["arrived"] = true
		(pr["rec"] as Dictionary)["event_t"] = _clock
		(pr["rec"] as Dictionary)["at"] = at
		return
	if not (_in[i] as Dictionary).is_empty():
		_leave(i)
