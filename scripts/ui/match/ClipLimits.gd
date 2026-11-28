class_name ClipLimits
extends RefCounted
## A real body's joint limits on the broadcast-made clips (reel feedback 2026-11-22: "some of the
## animations create some strange model contortion"). Rokoko's read of broadcast footage sometimes
## bends an elbow sideways or backwards, turns a wrist past where skin can follow, or folds a knee
## the wrong way: tools/oval3d/joint_audit.py measured every clip (umpire_bounce_01's right elbow 21
## deg past straight and 63 deg off its hinge; scoops and kicks 35-48 deg off the elbow hinge, where
## the Epic GASP clips stay within ~32). Each joint's rotation away from rest is split into its
## twist (about the bone) and its bend; the bend of a hinge (elbow, knee) is split again into the
## part on the hinge and the part off it, and each part is held inside the limit below. The GASP
## clips (jog, carry, idle, tackles) are left exactly as they are.
##
## Once per clip resource (the clips are shared by every player): ClipLimits.apply(ap, skel).

## deg. off: bend off the hinge; hyper: past straight; twist: about the bone; bend: any way.
const LIMITS := {
	"lowerarm_l": {"off": 35.0, "hyper": 10.0, "twist": 70.0},
	"lowerarm_r": {"off": 35.0, "hyper": 10.0, "twist": 70.0},
	"calf_l": {"off": 20.0, "hyper": 5.0, "twist": 35.0},
	"calf_r": {"off": 20.0, "hyper": 5.0, "twist": 35.0},
	"hand_l": {"twist": 70.0, "bend": 70.0},
	"hand_r": {"twist": 70.0, "bend": 70.0},
	"foot_l": {"twist": 35.0, "bend": 60.0},
	"foot_r": {"twist": 35.0, "bend": 60.0},
	"neck_01": {"twist": 70.0, "bend": 70.0},
	"head": {"twist": 60.0, "bend": 60.0},
}
## The hinge's axis in the elbow's and knee's own space (the flex way), measured off the GASP
## clips' bends (joint_audit.py: [1, 0, 0.02] at all four), and the bone each hangs from.
const HINGE := Vector3(1.0, 0.0, 0.0)
const PARENT := {"lowerarm_l": "upperarm_l", "lowerarm_r": "upperarm_r", "calf_l": "thigh_l", "calf_r": "thigh_r"}


## The slow gait loops (Oval3DAnim.GAITS: optical motion capture, as the run and the stand), named
## here so this file needs nothing that reaches the autoloads.
const GAITS := ["walk", "backstep", "backpedal", "shuffle_l", "shuffle_r", "side_run_l", "side_run_r"]


static func kept(clip: String) -> bool:
	return clip in ["jog", "carry", "idle", "sprint"] or clip in GAITS or clip.begins_with("tackle_")


static func apply(ap: AnimationPlayer, skel: Skeleton3D) -> void:
	var joints := _joints(skel)
	for clip in ap.get_animation_list():
		if kept(str(clip)):
			continue
		var a := ap.get_animation(clip)
		if a.has_meta("limited"):
			continue
		a.set_meta("limited", true)
		for t in a.get_track_count():
			if a.track_get_type(t) != Animation.TYPE_ROTATION_3D:
				continue
			var bone := str(a.track_get_path(t)).get_slice(":", 1)
			if not joints.has(bone):
				continue
			var j: Dictionary = joints[bone]
			for k in a.track_get_key_count(t):
				var q: Quaternion = a.track_get_key_value(t, k)
				a.track_set_key_value(t, k, (j["rest"] as Quaternion) * limit((j["rest"] as Quaternion).inverse() * q, j))


## Each limited bone: its rest rotation, its line (toward its first child), and for a hinge the
## rest pose's own bend (the MetaHuman rest has its elbows ~46 deg and knees ~7 deg bent).
static func _joints(skel: Skeleton3D) -> Dictionary:
	var out := {}
	for bone in LIMITS:
		var id := skel.find_bone(bone)
		if id < 0:
			continue
		var kids := skel.get_bone_children(id)
		var dir := Vector3.UP if kids.is_empty() else skel.get_bone_rest(kids[0]).origin.normalized()
		var rest := skel.get_bone_rest(id).basis.get_rotation_quaternion()
		var j := {"rest": rest, "dir": dir}
		j.merge(LIMITS[bone])
		if PARENT.has(bone):
			var pid := skel.find_bone(PARENT[bone])
			var pk := skel.get_bone_children(pid)
			var up := skel.get_bone_rest(pk[0]).origin.normalized()
			var seen := rest.inverse() * up
			var cr := seen.cross(dir)
			var bend := atan2(cr.length(), seen.dot(dir))
			j["rest_bend"] = bend if cr.dot(HINGE) >= 0.0 else -bend
		out[bone] = j
	return out


## A joint's rotation away from rest (`q`, its own space) held inside joint `j`'s limits.
static func limit(q: Quaternion, j: Dictionary) -> Quaternion:
	if q.w < 0.0:
		q = -q
	var d: Vector3 = j["dir"]
	var v := Vector3(q.x, q.y, q.z)
	var p := d * v.dot(d)
	var tw := Quaternion(p.x, p.y, p.z, q.w)
	tw = Quaternion.IDENTITY if tw.length() < 1e-6 else tw.normalized()
	var tw_ang := wrapf(2.0 * atan2(Vector3(tw.x, tw.y, tw.z).dot(d), tw.w), -PI, PI)
	var sw := q * tw.inverse()
	if sw.w < 0.0:
		sw = -sw
	var rv := Vector3.ZERO
	if sw.get_angle() > 1e-6:
		rv = sw.get_axis().normalized() * sw.get_angle()
	if j.has("off"):
		var h := rv.dot(HINGE)
		var o := rv - HINGE * h
		var off := deg_to_rad(float(j["off"]))
		if o.length() > off:
			o = o.normalized() * off
		h = maxf(h, -(float(j["rest_bend"]) + deg_to_rad(float(j["hyper"]))))
		rv = HINGE * h + o
	if j.has("bend") and rv.length() > deg_to_rad(float(j["bend"])):
		rv = rv.normalized() * deg_to_rad(float(j["bend"]))
	var lim := deg_to_rad(float(j["twist"]))
	tw_ang = clampf(tw_ang, -lim, lim)
	var swing := Quaternion.IDENTITY if rv.length() < 1e-6 else Quaternion(rv.normalized(), rv.length())
	return (swing * Quaternion(d, tw_ang)).normalized()
