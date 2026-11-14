class_name Oval3DAnim
extends RefCounted
## The 3D oval's animation controller (row 198, owned by the animation session; Oval3D.gd only
## calls step()). Picks each player's clip, facing and rate from his token and the ball, and
## advances his AnimationPlayer by dt. This default holds the prototype's jog / idle / carry logic.

const JOG_SPEED := 6.0
const RUN_FROM := 1.4          # m/s: slower than this he stands

var director: MatchDirector
var players: Array


func _init(p_director: MatchDirector, p_players: Array) -> void:
	director = p_director
	players = p_players


## Pose player i for this frame. holder = the index with the ball in his hands, or -1.
func step(i: int, p: Dictionary, holder: int, pos: Vector2, vel: Vector2, dt: float) -> void:
	var node: Node3D = p["node"]
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
		if ap.current_animation != "idle" and ap.current_animation != "":
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
