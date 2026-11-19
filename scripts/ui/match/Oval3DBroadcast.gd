class_name Oval3DBroadcast
extends RefCounted
## The match's TV coverage on the 3D oval (row 202, 2e): which camera the picture comes from, and
## where it points. Each camera works as a real broadcast camera does: it stands still on its
## mount and only pans, tilts and zooms to follow the play.
##
## The main camera (rule 2.93) is the real AFL main camera (Free TV Australia OP-33): on the
## centre line, 15 m up and 25 m back from the near boundary. It aims at the ball, its aim
## smoothed over the last half second of play as an operator's hand smooths it, and zooms so 57 m
## of ground are across the picture where it aims (about a third of the ground). On a phone the
## picture is taller than a TV picture (rule 2.105) at the same zoom: the width sets the lens.
## Nobody within 20 m of the lens is drawn (rule 2.101), so no supporter blocks the picture.
## Rule 2.111: the phone's picture is taller than TV's, so the main camera normally zooms in until
## its top and bottom are a TV picture's (about 26 m across), a strip of crowd and no sky. It
## zooms out to the wide shot (57 m across, the ball in the middle, sky over the stand) while a
## kick of 40 m or more is in the air, and while the players walk back for a centre bounce (after
## a goal, once its replay is over, and at the start of each quarter), then back in for the
## bounce. Each zoom is quick but eased, half a second of real time at any match speed.
##
## A set shot (rule 2.102, "do what happens IRL") cuts live to the camera behind the goals at the
## far end, behind the kicker's back (15 m up, 25 m back from that goal line), from when the man who
## marked lines up until a third of a second after the ball reaches the goals, then back to the
## main camera. Real TV frames that shot on the posts he kicks at, not on him (Seven, Adelaide v
## Geelong and Fox, Fremantle v St Kilda, 2025, measured on the 6.4 m gaps between the posts):
## 42 m across at the goal line, aimed 3.3 m up it, so the goal line sits two thirds down a
## 16:9 picture with the crowd behind the posts above. It holds still while he kicks.
##
## A ball-up around the ground (rule 2.103) cuts to about a second close on each ruckman while
## the pack settles, then back to the main camera just before the umpire throws it up. Real TV
## shoots those close-ups from its wing cameras (the centre one and one at each 50 m line, Free
## TV OP-33): the shot comes from the first of them with a clear line to the ruckman, so no other
## man stands in front of him.
##
## After a goal (rule 2.96) one replay: the last moments of the kick, from the same camera and
## framing as a set shot's (behind the far goals, on the posts), at half real speed (a 1.7 s kick and flight shows over 3.4 s), while play goes on
## underneath and the players walk back; the centre bounce waits for the replay to end. A skip
## (skip_replay) brings the picture back live at once. A behind gets none, except the deciding
## one (it is the last score and wins or levels the game), replayed after the siren.
##
## Times are match seconds as the view plays them (the speed the coach picked applied), so at 4x
## the picture is the 1x picture played four times as fast.

const EYE_UP := 15.0          # m above the ground
const EYE_BACK := 25.0        # m back from the boundary
const MAIN_WIDTH := 57.0      # m of ground across the picture where the main camera aims
const MAIN_SMOOTH := 0.5      # s of play the main camera's aim is averaged over
const AIM_Y := 1.0            # m: the camera aims this high over the ball's spot
const NEAR := 20.0            # m: nobody nearer the lens is drawn (rule 2.101)
const GOALS_WIDTH := 42.0     # m across the picture at the goal line it is kicked at
const GOALS_AIM_Y := 3.3      # m up the goal line the goals camera aims
const SHOT_TAIL := 0.33       # s on the goals camera after the ball reaches the goals
const CLOSE_WIDTH := 3.2      # m across the picture at a ruckman, close
const CLOSE_SMOOTH := 0.3     # s
const CLOSE_AIM_Y := 1.2      # m: his chest
const CLOSE_FROM := [2.15, 3.63, 4.95]  # director s into the pack: ruck one, ruck two, back wide
const WING_50 := MatchMotion.HALF_LEN - 50.0  # m along the wing to the 50 m line cameras
const CLEAR := 0.5            # m: a man nearer the sight line than this blocks the close-up
const REPLAY_RATE := 0.5      # the replay plays at half real speed
const REPLAY_BEFORE := 0.58   # director s of the replay before the kick
const REPLAY_AFTER := 0.23    # ...and after the ball reaches the goals
const LONG_KICK := 40.0       # m: a kick at least this long is watched on the wide shot
const ZOOM_S := 0.5           # real s a zoom takes, in or out
const CUT := 8.0              # m: a ball moved further than this in one frame was put back (a
                              # bounce after a goal, the change of ends); the camera goes straight there

var oval: Oval3D
var camera: Camera3D
var _trail: Array = []        # [[t, world aim]] over the last MAIN_SMOOTH s
var _t := 0.0                 # match seconds this broadcast has run
var _last_ball := Vector3.INF # where the ball was last frame
var shot := "main"            # the camera the picture comes from: "main" or "goals"
var _end_x := 0.0             # the goals camera's end: the goal line's x on the ground (+ or -)
var _tail := -1.0             # s left on the goals camera after the ball got there; -1 not yet
var _shot_k := -1            # the shot the goals camera is on (its event)
var _close_eye := Vector3.ZERO  # the wing camera the close-up is shot from
var _close_who := -1          # the ruckman the close-up is on; -1 none
var _close_trail: Array = []
var _rec: Array = []          # [{t, men: [[xform, rots, hip]], ball, x}] for a replay; director time
var _rec_k := -1              # the shot being recorded (its event); -1 none
var _kick_t := -1.0           # director time the ball left his boot; -1 not yet
var _score_t := -1.0          # ...and reached the goals
var _replay: Array = []       # the clip being replayed (a slice of _rec); empty when live
var _replay_end := 0.0        # its last record's time (director time)
var _replay_x := 0.0          # the goal line it was kicked at
var _replay_t := 0.0          # where the replay is (director time)
var _after_siren: Array = []  # the deciding behind's clip, for after the siren
var replaying := false        # the picture shows a replay
var _kick_wide := false       # a long kick's zoom out still running (rule 2.111)
var _zoom := 1.0              # 0 the normal TV-height shot, 1 the wide shot (rule 2.111)


func _init(p_oval: Oval3D) -> void:
	oval = p_oval
	camera = oval.camera
	camera.keep_aspect = Camera3D.KEEP_WIDTH
	camera.near = NEAR


## The main camera's mount, in the world (the ground turns under it at a change of ends; the
## camera stays on the near wing).
static func main_eye() -> Vector3:
	return Vector3(0.0, EYE_UP, MatchMotion.HALF_WID + EYE_BACK)


## One frame of the picture: `dt` match seconds since the last (0 places it at once), `wall`
## real seconds (0 while the match is paused).
func frame(dt: float, wall := 0.0) -> void:
	_t += dt
	_record()
	if replaying:
		_play_replay(wall)
		return
	var bp := oval.ball.global_position
	var aim := Vector3(bp.x, AIM_Y, bp.z)
	if dt <= 0.0 or bp.distance_to(_last_ball) > CUT:
		_trail.clear()
	_last_ball = bp
	var main_aim := _smooth(_trail, aim, MAIN_SMOOTH)
	_set_shot(dt)
	if replaying:
		_play_replay(0.0)
		return
	_set_close()
	if _close_who >= 0:
		var gp := ((oval.players[_close_who] as Dictionary)["node"] as Node3D).global_position
		_shoot(_close_eye, _smooth(_close_trail, Vector3(gp.x, CLOSE_AIM_Y, gp.z), CLOSE_SMOOTH), CLOSE_WIDTH)
	elif shot == "goals":
		_goals_shot(signf((oval.global_transform * Vector3(_end_x, 0.0, 0.0)).x))
	else:
		_shoot(main_eye(), main_aim, MAIN_WIDTH)
		var b: Dictionary = oval.director.ball
		if str(b.get("mode", "")) == "flight" and (b["from"] as Vector2).distance_to(b["to"]) >= LONG_KICK:
			_kick_wide = true
		elif _zoom >= 1.0:
			_kick_wide = false
		# A long kick's zoom always runs its whole half second ("B: steady half second"), so at
		# speed the picture is fully wide just after the ball lands, then eases back in.
		var want := 1.0 if _kick_wide or _wide() else 0.0
		if dt > 0.0:  # paused or placed at once: the zoom holds
			_zoom = move_toward(_zoom, want, (wall if wall > 0.0 else dt) / ZOOM_S)
		_tv_height(smoothstep(0.0, 1.0, _zoom))


## Rule 2.111: besides a long kick, the main camera is wide for the opening picture of each
## quarter and while the players set up for a centre bounce, until the umpire is about to
## bounce it. (A centre bounce's beat is named for what follows the bounce; its first phase is the
## centre set-up.)
func _wide() -> bool:
	var d = oval.director
	if d._beat.is_empty():
		return true
	if d.bounce_next() or d._pi >= d._phases.size() or d._phases.is_empty():
		return false
	var first: Dictionary = d._phases[0]
	if str(first.get("t", "")) != "setup" or str(first.get("mode", "")) != "centre":
		return false
	return str((d._phases[d._pi] as Dictionary).get("t", "")) == "setup"


## The main camera, aimed and zoomed for the wide shot, narrowed to the TV picture's height:
## `wide` 0 is a 16:9 picture's top and bottom on the phone's taller picture, 1 the wide shot.
func _tv_height(wide: float) -> void:
	var vs := camera.get_viewport().get_visible_rect().size
	var tw := tan(deg_to_rad(camera.fov) * 0.5)
	var tv := tw * 9.0 / 16.0 * vs.x / vs.y  # the TV picture's half-height, as a half-width here
	camera.fov = rad_to_deg(2.0 * atan(lerpf(tv, tw, wide)))


## The kick the goals camera waits for is through. The kicker's pause on his mark (before the
## kick) reads as no shot at all, so the camera holds until play is past the kick's own event.
func _past_shot() -> bool:
	var d = oval.director
	if d._beat.is_empty():
		return d.cursor > _shot_k
	var bk := int(d._beat["k"])
	return bk > _shot_k or (bk == _shot_k and d._pi >= d._phases.size())


## Rule 2.102: on the goals camera from the line-up to SHOT_TAIL after the ball gets there.
func _set_shot(dt: float) -> void:
	var s := oval.director.shot_now()
	if shot == "main":
		if not s.is_empty() and not bool(s["set"]) and str(s["phase"]) == "celebrate" 				and _score_t >= 0.0 and oval.director.time > _score_t + REPLAY_AFTER:
			# A shot from general play, watched on the main camera: its replay once it is through.
			_after_score()
			return
		if not s.is_empty() and bool(s["set"]) and str(s["phase"]) != "celebrate":
			shot = "goals"
			_end_x = (s["to"] as Vector2).x
			_shot_k = int(s["k"])
			_tail = -1.0
		return
	if _tail < 0.0 and ((s.is_empty() and _past_shot()) or (not s.is_empty() and str(s["phase"]) == "celebrate")):
		_tail = SHOT_TAIL
	elif _tail >= 0.0:
		_tail -= dt
		if _tail <= 0.0:
			shot = "main"
			_tail = -1.0
			_after_score()


## Rule 2.103: the close-up on each ruckman in a ball-up's wait, by how long the pack has stood.
func _set_close() -> void:
	var b := oval.director.ballup_now()
	var who := -1
	if not b.is_empty():
		var t := float(b["t"])
		for i in range(2):
			if t >= float(CLOSE_FROM[i]) and t < float(CLOSE_FROM[i + 1]):
				who = int((b["rucks"] as Array)[i])
	if who != _close_who and who >= 0:
		_close_eye = _clear_eye(who)
		_close_trail.clear()
	_close_who = who


## The first wing camera (the centre one, then the nearer 50 m one, then the other) with a clear
## line to `who`: nobody else nearer that line than CLEAR between the lens and him.
func _clear_eye(who: int) -> Vector3:
	var at: Vector3 = ((oval.players[who] as Dictionary)["node"] as Node3D).global_position
	var a2 := Vector2(at.x, at.z)
	var side := signf(at.x) if at.x != 0.0 else 1.0
	var eyes := [main_eye(), main_eye() + Vector3(side * WING_50, 0.0, 0.0),
			main_eye() - Vector3(side * WING_50, 0.0, 0.0)]
	for eye in eyes:
		var e2 := Vector2((eye as Vector3).x, (eye as Vector3).z)
		var clear := true
		for i in range(oval.players.size()):
			if i == who:
				continue
			var gp: Vector3 = ((oval.players[i] as Dictionary)["node"] as Node3D).global_position
			var g2 := Vector2(gp.x, gp.z)
			var q := Geometry2D.get_closest_point_to_segment(g2, e2, a2)
			if q.distance_to(g2) < CLEAR and q.distance_to(a2) > 0.3:
				clear = false
				break
		if clear:
			return eye
	return eyes[0]


## Rule 2.96: while a shot at goal is on, every man's place and pose, the umpires' and the
## ball's, each frame (director time), for its replay.
func _record() -> void:
	var s := oval.director.shot_now()
	if s.is_empty():
		if _score_t < 0.0:
			_rec_k = -1
			_rec.clear()
		return
	var k := int(s["k"])
	if k != _rec_k:
		_rec_k = k
		_rec.clear()
		_kick_t = -1.0
		_score_t = -1.0
	var phase := str(s["phase"])
	var now := oval.director.time
	if phase == "flight" and _kick_t < 0.0:
		_kick_t = now
	if (phase == "emit" or phase == "celebrate") and _score_t < 0.0:
		_score_t = now
	if _score_t >= 0.0 and now > _score_t + REPLAY_AFTER + 0.1:
		return
	var men := []
	for f in oval.players + oval.umpires:
		var skel: Skeleton3D = (f as Dictionary)["skel"]
		var rots := []
		for b in range(skel.get_bone_count()):
			rots.append(skel.get_bone_pose_rotation(b))
		men.append([((f as Dictionary)["node"] as Node3D).transform, rots, skel.get_bone_pose_position(0)])
	_rec.append({"t": now, "men": men, "ball": oval.ball.transform, "x": (s["to"] as Vector2).x})


## The ball has reached the goals: a goal's replay now; the deciding behind's after the siren.
func _after_score() -> void:
	var k := _rec_k
	if k < 0 or _kick_t < 0.0 or _score_t < 0.0:
		return
	var clip := []
	for r in _rec:
		if float(r["t"]) >= _kick_t - REPLAY_BEFORE and float(r["t"]) <= _score_t + REPLAY_AFTER:
			clip.append(r)
	_rec_k = -1
	_rec.clear()
	_score_t = -1.0
	if clip.size() < 2:
		return
	if str((oval.director.events[k] as Dictionary).get("kind", "")) == "goal":
		_start_replay(clip)
	elif oval.director.deciding_behind(k):
		_after_siren = clip


## The deciding behind's replay, once the siren has gone (rule 2.96). False when there is none.
func replay_after_siren() -> bool:
	if _after_siren.is_empty():
		return false
	_start_replay(_after_siren)
	_after_siren = []
	return true


func _start_replay(clip: Array) -> void:
	_replay = clip
	_replay_t = float(clip[0]["t"])
	_replay_end = float(clip[-1]["t"])
	_replay_x = float(clip[0]["x"])
	replaying = true
	shot = "goals"


## Back to the live picture: the replay is over, or the coach skipped it.
func skip_replay() -> void:
	if not replaying:
		return
	replaying = false
	_replay = []
	shot = "main"
	_trail.clear()
	_zoom = 1.0  # rule 2.111: back from the replay on the ground and crowd, then in for the bounce


## One frame of the replay, `wall` real seconds on: every recorded man, umpire and the ball put
## where they were (between the two nearest records), over the live picture's.
func _play_replay(wall: float) -> void:
	_replay_t += wall * REPLAY_RATE
	if _replay_t > _replay_end:
		skip_replay()
		frame(0.0)
		return
	var j := 0
	while j < _replay.size() - 2 and float(_replay[j + 1]["t"]) < _replay_t:
		j += 1
	var r0: Dictionary = _replay[j]
	var r1: Dictionary = _replay[j + 1]
	var span := float(r1["t"]) - float(r0["t"])
	var u := clampf((_replay_t - float(r0["t"])) / span, 0.0, 1.0) if span > 0.0 else 0.0
	var figs: Array = oval.players + oval.umpires
	for i in range(mini(figs.size(), (r0["men"] as Array).size())):
		var f: Dictionary = figs[i]
		var m0: Array = r0["men"][i]
		var m1: Array = r1["men"][i]
		(f["node"] as Node3D).transform = (m0[0] as Transform3D).interpolate_with(m1[0], u)
		var skel: Skeleton3D = f["skel"]
		var q0: Array = m0[1]
		var q1: Array = m1[1]
		for b in range(q0.size()):
			skel.set_bone_pose_rotation(b, (q0[b] as Quaternion).slerp(q1[b], u))
		skel.set_bone_pose_position(0, (m0[2] as Vector3).lerp(m1[2], u))
	oval.ball.transform = (r0["ball"] as Transform3D).interpolate_with(r1["ball"], u)
	_goals_shot(signf((oval.global_transform * Vector3(_replay_x, 0.0, 0.0)).x))


## The goals camera for a kick at the goals at world end `end` (+1 or -1): it stands behind the
## other goals and holds on these posts.
func _goals_shot(end: float) -> void:
	var eye := Vector3(-end * (MatchMotion.HALF_LEN + EYE_BACK), EYE_UP, 0.0)
	_shoot(eye, Vector3(end * MatchMotion.HALF_LEN, GOALS_AIM_Y, 0.0), GOALS_WIDTH)


## `aim` added to `trail` (now), and the mean of the trail's last `over` seconds.
func _smooth(trail: Array, aim: Vector3, over: float) -> Vector3:
	trail.append([_t, aim])
	while trail.size() > 1 and _t - float(trail[0][0]) > over:
		trail.pop_front()
	var sum := Vector3.ZERO
	for e in trail:
		sum += e[1] as Vector3
	return sum / float(trail.size())


## The camera at `eye`, aimed at `aim`, zoomed so `width` metres are across the picture there.
func _shoot(eye: Vector3, aim: Vector3, width: float) -> void:
	camera.global_position = eye
	camera.look_at(aim, Vector3.UP)
	camera.fov = rad_to_deg(2.0 * atan(width * 0.5 / eye.distance_to(aim)))
	# Where the picture looks, on the ground's own frame (the overlays size their names by it).
	var at := oval.global_transform.affine_inverse() * aim
	oval._look = Vector3(at.x, 0.0, at.z)
