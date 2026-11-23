class_name Oval3DInjury
extends RefCounted
## In-match injuries on the 3D oval (row 202 2e), as AFL TV shows them. MatchDirector decides
## when and where (MatchDirector.hurt: he goes down in his last contest before the swap, lies
## there, walks to the interchange gate); this draws it: the fall, lying hurt, getting up, the
## walk off with his trainers beside him, and the walk on past the gate once his replacement is
## on. Looks only: it reads the director and never writes to it.
##
## The motion is Mixamo's (tools/oval3d/injury: retarget_mixamo.py onto our rig, baked into
## assets/oval3d/injury_clips.glb; Mixamo's terms allow its motion in games, and no Mixamo file is
## in the repo). Clip time runs on the 3D picture's own clock (Oval3D.sync's dt), as every clip does;
## the stages run on the director's (MatchDirector.down_s), as his token does.

const CLIPS_GLB := "res://assets/oval3d/injury_clips.glb"
## What each kind of injury plays: the fall (from a run or a contest), and the get-up. A kind not
## here plays "soft". Real AFL broadcasts (2018-2025, timed frame by frame): a concussed man drops
## and lies still face down; a knee or an ankle goes down at once and stays down; a hamstring or
## other strain is on the turf within a second or two and back up within a few seconds.
const PLAN := {
	"concussion": {"fall": "knocked_out", "up": "getting_up"},
	"knee": {"fall": "falling_down", "up": "getting_up"},
	"ankle": {"fall": "falling_down", "up": "getting_up"},
	"foot": {"fall": "falling_down", "up": "getting_up"},
	"shoulder": {"fall": "falling_down", "up": "getting_up"},
	"soft": {"fall": "falling_down", "up": "getting_up"},
}
## The walk off, by kind (the loop he walks off on): a hurt arm carried against the body, a hurt
## leg limped on. Its pace in m/s at rate 1 is read off the clip (_walk_speed).
const WALK := {"shoulder": "injured_arm_walk", "hand": "injured_arm_walk"}
const WALK_DEFAULT := "injured_walk"
## Clips that loop (the rest play once and hold their last pose).
const LOOPS := ["injured_walk", "injured_arm_walk", "kneeling", "fallen_idle", "injured_idle",
		"injured_hurting_idle", "injured_stumble_idle", "sitting_dazed"]
## Seconds of clip a change of clip blends over, when the two poses already match (_entry).
const BLEND := 0.25
## Seconds short of a played-once clip's end that it holds at.
const HOLD_SHORT := 0.004
## m/s (picture) the gap between his get-up's last hips and his walking token closes at: slow
## enough to read as his own steps.
const OFF_CLOSE := 0.5
## Picture seconds the get-up is given at most (the clip itself runs 8 s; it plays faster to fit).
const UP_MAX := 4.0
## The trainers: how soon after he goes down they set off (director seconds), how far beside him
## they stand and walk.
const REACT := MatchDirector.TRAINER_REACT
const BESIDE := 0.85
## m from his body's line a trainer kneels at while he is down (beside his hips, never on him).
const KNEEL_OFF := 0.7
## Trainers out to him: one walks a strained man off (the footage: one trainer beside him), two
## for the rest.
const TRAINERS := 2
## m he walks past the gate before he is out of the picture (behind the bench).
const PAST_GATE := 4.0

var oval: Oval3D
var scenes: Array = []        # {pid, kind, how, side, slot, p, stage, ct, t0, yaw, off, trainers}
var _clips := {}              # clip name -> Animation (on the figures' skeleton path)
var _len := {}                # clip name -> length
var _entry := {}              # "a>b" -> clip time of b whose pose best matches a's end
var _have := false


func _init(p_oval: Oval3D) -> void:
	oval = p_oval


## The clips, on every figure (the players and spares share one animation library).
func load_clips(p: Dictionary) -> void:
	var ap: AnimationPlayer = p["anim"]
	var skel: Skeleton3D = p["skel"]
	var key := str(ap.get_node(ap.root_node).get_path_to(skel))
	var ps: PackedScene = load(CLIPS_GLB) if ResourceLoader.exists(CLIPS_GLB) else null
	if ps == null:
		return
	var n := ps.instantiate()
	var src: AnimationPlayer = n.find_children("*", "AnimationPlayer", true, false)[0]
	var lib := ap.get_animation_library("")
	for name in src.get_animation_list():
		var a: Animation = src.get_animation(name).duplicate(true)
		for t in range(a.get_track_count()):
			var path := a.track_get_path(t)
			var bone := path.get_concatenated_subnames()
			if bone == "":
				bone = str(path.get_name(path.get_name_count() - 1))
			a.track_set_path(t, NodePath(key + ":" + bone))
		a.loop_mode = Animation.LOOP_LINEAR if str(name) in LOOPS else Animation.LOOP_NONE
		if str(name).ends_with("_walk"):
			_in_place(a)
		_clips[name] = a
		_len[name] = a.length
		if not lib.has_animation(name):
			lib.add_animation(name, a)
	n.free()
	_have = not _clips.is_empty()


## A walk loop walked on the spot: Mixamo's walks carry the hips forward over the turf, but the
## figure is moved by his token, so the hips' steady drift over a loop is taken out (their sway
## stays). Without it the hips run ahead and snap back every loop.
func _in_place(a: Animation) -> void:
	for t in range(a.get_track_count()):
		if a.track_get_type(t) != Animation.TYPE_POSITION_3D:
			continue
		if a.track_get_path(t).get_concatenated_subnames() != "pelvis":
			continue
		var n := a.track_get_key_count(t)
		if n < 2:
			return
		var t0 := a.track_get_key_time(t, 0)
		var t1 := a.track_get_key_time(t, n - 1)
		var drift: Vector3 = a.track_get_key_value(t, n - 1) - a.track_get_key_value(t, 0)
		for k in range(n):
			var f := (a.track_get_key_time(t, k) - t0) / maxf(1e-3, t1 - t0)
			a.track_set_key_value(t, k, (a.track_get_key_value(t, k) as Vector3) - drift * f)
		return


func has(name: String) -> bool:
	return _clips.has(name)


## Whether slot i's figure is the hurt man's, drawn here this frame (Oval3D.sync leaves it alone).
func owns(i: int) -> bool:
	for s in scenes:
		if int(s["slot"]) == i:
			return true
	return false


func _kind_plan(kind: String) -> Dictionary:
	return PLAN.get(kind, PLAN["soft"])


func _walk_clip(kind: String) -> String:
	var w := str(WALK.get(kind, WALK_DEFAULT))
	return w if _clips.has(w) else ""


## A frame: new hurt men from the director, then each scene's stage, pose and place.
func step(dt: float) -> void:
	if not _have:
		return
	var d: MatchDirector = oval.director
	for id in d.hurt:
		if not _scene_of_slot(int(id)).is_empty():
			continue
		var r: Dictionary = d.hurt[id]
		# He pulls up in his own strides (the run loop slows with his token); the fall starts
		# once he has pulled up, so he never slides along the turf in a falling clip.
		if d.time - float(r["t0"]) < MatchDirector.PULL_UP:
			continue
		if _scene_of_pid(str(r["pid"])).is_empty():
			_begin(int(id), r)
	for s in scenes.duplicate():
		_step_scene(s, dt)


func _scene_of_slot(i: int) -> Dictionary:
	for s in scenes:
		if int(s["slot"]) == i:
			return s
	return {}


func _scene_of_pid(pid: String) -> Dictionary:
	for s in scenes:
		if str(s["pid"]) == pid:
			return s
	return {}


func _begin(i: int, r: Dictionary) -> void:
	var p: Dictionary = oval.players[i]
	var kind := str(r["kind"])
	var plan := _kind_plan(kind)
	var node: Node3D = p["node"]
	# Out of whatever the run loop or a scoop had him in.
	if oval.anim != null:
		oval.anim._once[i] = {}
		oval.anim._gap[i] = Vector2.ZERO
	var s := {"pid": str(r["pid"]), "kind": kind, "side": int(r["side"]), "slot": i, "p": p,
			"stage": "fall", "ct": 0.0, "t0": float(r["t0"]), "yaw": node.rotation.y,
			"off": Vector2.ZERO, "trainers": [], "clip": str(plan["fall"]), "seen": false,
			"down": float(r["down"])}
	(p["anim"] as AnimationPlayer).play(str(plan["fall"]), BLEND)
	scenes.append(s)
	if oval.crew != null:
		var n := TRAINERS if MatchDirector.waits_for_trainers(kind) else 1
		s["trainers"] = oval.crew.take_trainers(int(r["side"]), Vector2(node.position.x, node.position.z), n)


## His replacement has the slot (MatchDirector._sub): the hurt man goes on in a spare figure,
## dressed as him, in the same pose, and walks the rest of the way off on his own clock.
func hand_off(i: int, p: Dictionary) -> bool:
	var s := _scene_of_slot(i)
	if s.is_empty():
		return false
	var q: Dictionary = oval.take_spare(int(s["side"]), p)
	var ap: AnimationPlayer = p["anim"]
	var aq: AnimationPlayer = q["anim"]
	if ap.current_animation != "":
		aq.play(ap.current_animation)
		aq.seek(ap.current_animation_position, true)
	s["p"] = q
	s["slot"] = -1
	(p["ring"] as Node3D).position = Vector3(0.0, 0.03, 0.0)
	return true


func _step_scene(s: Dictionary, dt: float) -> void:
	var d: MatchDirector = oval.director
	var p: Dictionary = s["p"]
	var node: Node3D = p["node"]
	var ap: AnimationPlayer = p["anim"]
	var plan := _kind_plan(str(s["kind"]))
	var e := d.time - float(s["t0"])
	# Director seconds since this scene's last frame: the director's clock is not always the
	# picture's times TEMPO (it runs on through dead play), and his walk and his trainers keep to it.
	var dd := maxf(0.0, d.time - float(s.get("t_last", d.time)))
	s["t_last"] = d.time
	var down := float(s["down"])
	var slot := int(s["slot"])
	var tok_pos: Vector2 = d.tokens[slot]["pos"] if slot >= 0 else Vector2.INF
	var stage := str(s["stage"])
	var up := str(plan["up"])
	var walk := _walk_clip(str(s["kind"]))
	# The get-up starts so that he is on his feet as the director has him walk (down_s).
	var up_len := 0.0
	if up != "":
		up_len = minf(UP_MAX, float(_len[up]) - _entry_t(str(plan["fall"]), up))
	if stage == "fall" and e >= down - up_len * MatchDirector.TEMPO:
		if up != "":
			_switch(s, up, _entry_t(str(s["clip"]), up))
			s["rate"] = (float(_len[up]) - float(s["ct"])) / maxf(0.1, up_len)
			stage = "up"
		else:
			stage = "walk"
	if stage == "up" and e >= down:
		stage = "walk"
	if stage == "walk" and str(s["stage"]) != "walk":
		if walk != "":
			_switch(s, walk, 0.0)
		s["walk_t"] = e
	s["stage"] = stage
	# The clip.
	var rate := float(s.get("rate", 1.0)) if stage == "up" else 1.0
	var moved := Vector2.ZERO
	if stage == "walk":
		var at := Vector2(node.position.x, node.position.z)
		var to: Vector2 = tok_pos if slot >= 0 else _past_gate()
		if slot < 0 and dt > 0.0:
			var pace := MatchDirector.walk_pace(str(s["kind"]))
			to = at + (to - at).limit_length(pace * dd)
		# The gap from his get-up's last hips to his token closes over the first steps.
		var off: Vector2 = s["off"]
		s["off"] = off - off.limit_length(OFF_CLOSE * dt)
		var want := to + (s["off"] as Vector2) if slot >= 0 else to
		moved = want - at
		node.position = Vector3(want.x, 0.0, want.y)
		if moved.length() > 0.002:
			node.rotation.y = rotate_toward(node.rotation.y, atan2(moved.x, moved.y), Oval3DAnim.TURN * 0.5 * dt)
		if walk != "" and dt > 0.0:
			var speed := moved.length() / dt
			rate = clampf(speed / maxf(0.1, _walk_speed(walk)), 0.0, 2.0)
		if slot < 0 and at.distance_to(_past_gate()) < 0.2:
			_end(s)
			return
	var clip := str(s["clip"])
	if ap.current_animation != clip:
		ap.play(clip, BLEND)
		ap.seek(float(s["ct"]), true)
	if dt > 0.0:
		var adv := dt * rate
		var a: Animation = _clips.get(clip)
		if a != null and a.loop_mode == Animation.LOOP_NONE:
			# A clip that has ended holds its last pose: kept a hair short of its end, so the
			# player never stops (a stopped player has no pose to blend the next clip from).
			adv = clampf(float(_len[clip]) - HOLD_SHORT - float(s["ct"]), 0.0, adv)
		s["ct"] = float(s["ct"]) + adv
		ap.advance(adv)
		if s.has("to_tf"):
			s["blend_e"] = float(s["blend_e"]) + adv
			var w := clampf(float(s["blend_e"]) / BLEND, 0.0, 1.0)
			var ft: Transform3D = s["from_tf"]
			var tt: Transform3D = s["to_tf"]
			if stage == "walk":
				# Walking, his token places him on the new clip's anchor; while the old pose
				# still shows, he is held back toward the old anchor by the part not yet blended.
				node.basis = ft.basis.slerp(tt.basis, w)
				var sk: Skeleton3D = p["skel"]
				var drawn := (node.get_parent() as Node3D).global_transform.affine_inverse() \
						* sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
				var keep: Vector3 = (s["hips_at"] as Vector3) + (node.position - tt.origin)
				node.position += Vector3(keep.x - drawn.x, 0.0, keep.z - drawn.z) * (1.0 - w)
			else:
				# Turned part way, and placed so his drawn hips stay where they were at the
				# switch (a mix of two poses under a turning frame would carry them off).
				node.transform = ft.interpolate_with(tt, w)
				var sk: Skeleton3D = p["skel"]
				var drawn := (node.get_parent() as Node3D).global_transform.affine_inverse() \
						* sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin
				var keep: Vector3 = s["hips_at"]
				node.position += Vector3(keep.x - drawn.x, 0.0, keep.z - drawn.z) * (1.0 - w)
			if w >= 1.0:
				s.erase("to_tf")
	_ring(p)
	_trainers(s, dt, dd)


## Switch scene s to clip b from clip time `from`: the figure is moved and turned so b's hips
## start where a's are now (each clip carries its own run over the turf), no slide, no jump.
func _switch(s: Dictionary, b: String, from: float) -> void:
	var p: Dictionary = s["p"]
	var node: Node3D = p["node"]
	var ap: AnimationPlayer = p["anim"]
	var anim: Oval3DAnim = oval.anim
	# His hips as drawn now (whatever blend is still showing), in the node's parent's frame.
	var sk: Skeleton3D = p["skel"]
	var ha := (node.get_parent() as Node3D).global_transform.affine_inverse() * sk.global_transform \
			* sk.get_bone_global_pose(sk.find_bone("pelvis"))
	var hb := anim._clip_hips(ap, b, from)
	var yaw := anim._yaw_of(ha.basis) - anim._yaw_of(hb.basis)
	var basis := Basis(Vector3.UP, yaw)
	var o := ha.origin - basis * hb.origin
	# The crossfade mixes a's pose and b's under one transform, so the figure moves from a's
	# anchor to b's over the same BLEND (else his hips jump by the gap between the anchors).
	s["from_tf"] = node.transform
	s["to_tf"] = Transform3D(basis, Vector3(o.x, 0.0, o.z))
	s["blend_e"] = 0.0
	s["hips_at"] = ha.origin
	s["clip"] = b
	s["ct"] = from
	var slot := int(s["slot"])
	if slot >= 0:
		var tp: Vector2 = oval.director.tokens[slot]["pos"]
		s["off"] = Vector2(o.x, o.z) - tp
	ap.play(b, BLEND)
	# No update here: an immediate update shows b in full and loses the crossfade.
	ap.seek(from)


## Where scene s's man's hips are drawn, in the world (Vector3.ZERO for no scene).
func hips(s: Dictionary) -> Vector3:
	if s.is_empty():
		return Vector3.ZERO
	var p: Dictionary = s["p"]
	var sk: Skeleton3D = p["skel"]
	return sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin


## His club's ring under his hips (lying, his feet are a metre from them).
func _ring(p: Dictionary) -> void:
	var sk: Skeleton3D = p["skel"]
	var node: Node3D = p["node"]
	var hips := node.global_transform.affine_inverse() * (sk.global_transform * sk.get_bone_global_pose(sk.find_bone("pelvis")).origin)
	(p["ring"] as Node3D).position = Vector3(hips.x, 0.03, hips.z)


## The time in clip b whose pose best matches clip a's last frame (the big joints' turns), so the
## get-up starts from the pose the fall left him in (a sitting man does not lie down to get up).
func _entry_t(a: String, b: String) -> float:
	var key := a + ">" + b
	if _entry.has(key):
		return float(_entry[key])
	var best := 0.0
	if _clips.has(a) and _clips.has(b):
		var ca: Animation = _clips[a]
		var cb: Animation = _clips[b]
		var bones := ["pelvis", "spine_02", "thigh_l", "thigh_r", "calf_l", "calf_r", "upperarm_l", "upperarm_r", "head"]
		var ta := _rot_tracks(ca, bones)
		var tb := _rot_tracks(cb, bones)
		var end := ca.length
		var bd := INF
		# Only the first two thirds of b: its end is him standing.
		var t := 0.0
		while t <= cb.length * 0.66:
			var dsum := 0.0
			for bn in bones:
				if ta.has(bn) and tb.has(bn):
					var qa := ca.rotation_track_interpolate(int(ta[bn]), end)
					var qb := cb.rotation_track_interpolate(int(tb[bn]), t)
					dsum += qa.angle_to(qb) if bn != "pelvis" else 0.0
			# The pelvis: how it lies (on his back, sitting) in the figure's own frame, ignoring
			# which way he faces.
			if ta.has("pelvis") and tb.has("pelvis"):
				var ua := Basis(ca.rotation_track_interpolate(int(ta["pelvis"]), end)) * Vector3.UP
				var ub := Basis(cb.rotation_track_interpolate(int(tb["pelvis"]), t)) * Vector3.UP
				dsum += 2.0 * absf(ua.y - ub.y)
			if dsum < bd:
				bd = dsum
				best = t
			t += 1.0 / 15.0
	_entry[key] = best
	return best


func _rot_tracks(a: Animation, bones: Array) -> Dictionary:
	var out := {}
	for k in range(a.get_track_count()):
		if a.track_get_type(k) != Animation.TYPE_ROTATION_3D:
			continue
		var b := a.track_get_path(k).get_concatenated_subnames()
		if b in bones:
			out[b] = k
	return out


var _walk_speeds := {}


## m/s a walk loop covers at rate 1 (its feet over the turf), measured once on the first figure.
func _walk_speed(name: String) -> float:
	if not _walk_speeds.has(name):
		_walk_speeds[name] = oval.anim._measure_loop(oval.players[0], name) if oval.anim != null else 1.3
		(oval.players[0]["anim"] as AnimationPlayer).play("idle")
	return float(_walk_speeds[name])


## The point past the gate where he is out of the picture: through the gate, behind the bench.
func _past_gate() -> Vector2:
	var g := oval.director.gate
	return g + g.normalized() * PAST_GATE


func _end(s: Dictionary) -> void:
	((s["p"] as Dictionary)["ring"] as Node3D).position = Vector3(0.0, 0.03, 0.0)
	oval.return_spare(int(s["side"]), s["p"])
	if oval.crew != null:
		oval.crew.release_trainers(s["trainers"])
	scenes.erase(s)


## The picture cut away (a replay, a change of ends): a hurt man already replaced is off.
func after_cut() -> void:
	for s in scenes.duplicate():
		if int(s["slot"]) < 0:
			_end(s)


## His trainers: run to him once they see him go down and kneel beside his hips, one either side
## of his body (never over his legs); stand when he gets up; then walk off beside him.
func _trainers(s: Dictionary, dt: float, ddt: float) -> void:
	var tr: Array = s["trainers"]
	if tr.is_empty() or oval.crew == null:
		return
	var d: MatchDirector = oval.director
	var p: Dictionary = s["p"]
	var node: Node3D = p["node"]
	var sk: Skeleton3D = p["skel"]
	var hips3 := hips(s)
	var head3 := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("head")).origin
	var at := Vector2(hips3.x, hips3.z)
	var stage := str(s["stage"])
	# His body's line on the turf (hips to head); standing, the way he faces.
	var axis := Vector2(head3.x - hips3.x, head3.z - hips3.z)
	if stage == "walk" or axis.length() < 0.35:
		axis = Vector2(sin(node.rotation.y), cos(node.rotation.y))
	axis = axis.normalized()
	var side := Vector2(axis.y, -axis.x)
	var go := d.time - float(s["t0"]) >= REACT
	var walking := stage == "walk"
	for j in range(tr.size()):
		var c: Dictionary = tr[j]
		var sgn := 1.0 if j == 0 else -1.0
		var n3: Node3D = c["node"]
		var here := Vector2(n3.position.x, n3.position.z)
		var want := at + side * sgn * (BESIDE if walking else KNEEL_OFF)
		var pace := MatchDirector.TRAINER_RUN
		if walking:
			pace = MatchDirector.walk_pace(str(s["kind"])) * 1.3
		if not go:
			want = here
		# Kneeling while he is down: down, hold, and up again as he gets up.
		var pose := ""
		var kt := float(c.get("kt", 0.0))
		var kp := str(c.get("kpose", ""))
		var there := here.distance_to(want) < 0.2
		if stage == "fall" and go and there and has("kneel_down"):
			if kp == "":
				kp = "kneel_down"
				kt = 0.0
			elif kp == "kneel_down" and kt >= float(_len["kneel_down"]) - 0.05:
				kp = "kneeling"
		elif kp == "kneel_down" or kp == "kneeling":
			kp = "kneel_up"
			kt = 0.0
		elif kp == "kneel_up" and kt >= float(_len["kneel_up"]) - 0.05:
			kp = ""
		if kp != "":
			pose = kp
			want = here
			kt += dt
		c["kpose"] = kp
		c["kt"] = kt
		oval.crew.move_to(c, want, at, pace, ddt, walking, pose)


