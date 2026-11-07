class_name PlayerMarks
extends RefCounted
## Tired and hurt players on the oval and the bench strip (T3.R10, director
## 2026-10-18: "A tired or injured player is told apart on live view and bench
## strip without a tap (short mark, words on long press, no fatigue
## percentage)"). A short drawn mark beside the disc says which, by its shape
## and not its colour alone: a cross for hurt, a near-empty tank for tired. A
## long press on the disc puts it in words.
##
## Read only: built from the events already played and, for your own side, the
## legs the match has recorded. Nothing here reaches the sim.

const TIRED := "tired"
const HURT := "hurt"


## pid -> {mark, words}: who carries a mark now. `played` is the match's events
## and `upto` how many of them the view has shown; `injuries` the match's injury records (MatchSim
## injuries, for the kind); `energy` pid -> legs for your own side's players
## (empty when the match is not yours to coach). A hurt man's mark outranks a
## tired one.
static func build(played: Array, upto: int, injuries: Array, energy: Dictionary) -> Dictionary:
	var out := {}
	for pid in energy:
		if float(energy[pid]) < MatchNotes.EMPTY:
			out[str(pid)] = {"mark": TIRED, "words": "Tired: running on empty"}
	var kinds := {}
	for rec in injuries:
		kinds[str((rec as Dictionary).get("id", ""))] = str((rec as Dictionary).get("kind", ""))
	for i in range(mini(upto, played.size())):
		var ev: Dictionary = played[i]
		if str(ev.get("kind", "")) != "injury":
			continue
		var pid := str(ev.get("player_id", ""))
		if pid == "":
			continue
		out[pid] = {"mark": HURT, "kind": str(kinds.get(pid, "")),
				"words": "Injured: " + hurt_words(str(kinds.get(pid, "")))}
	return out


## "hamstring strain", "sprained ankle", "concussion": the coach's word for the
## injury without its article.
static func hurt_words(kind: String) -> String:
	var w := Injuries.wording(kind)
	for art in ["a ", "an "]:
		if w.begins_with(art):
			return w.substr(art.length())
	return w


## The long-press words for a marked player, where he is now: a hurt man on the
## bench is done for the day; one still on the ground plays on hurt.
static func words(state: Dictionary, on_bench: bool) -> String:
	if str(state.get("mark", "")) == HURT:
		return str(state["words"]) + (", out for the day" if on_bench else ", playing on")
	return str(state.get("words", ""))


## The mark beside a disc of radius r at p: a small dark badge on the disc's
## upper right holding the cross or the tank. The badge's own shape tells the
## two apart; the hurt badge is also red, the tired one cream.
static func paint(ci: CanvasItem, p: Vector2, r: float, mark: String, aa: bool) -> void:
	var br := badge_radius(r)
	var c := badge_centre(p, r)
	# Hurt: a white cross on red. Tired: a dark tank on cream, so it stands off
	# a black or navy jumper as well as the grass.
	var cream := Color(0.96, 0.95, 0.92)
	var dark := Color(0.07, 0.07, 0.08)
	var ink := cream if mark == HURT else dark
	var back := Color(0.62, 0.16, 0.12) if mark == HURT else cream
	ci.draw_circle(c, br + 1.5, dark)
	ci.draw_circle(c, br, back)
	if mark == HURT:
		# A plain cross, the trainers' mark.
		var arm := br * 0.62
		var w := maxf(1.6, br * 0.36)
		ci.draw_rect(Rect2(c.x - arm, c.y - w * 0.5, arm * 2.0, w), ink)
		ci.draw_rect(Rect2(c.x - w * 0.5, c.y - arm, w, arm * 2.0), ink)
	else:
		# A tank near empty: an upright gauge, the bottom quarter filled.
		var gw := br * 0.9
		var gh := br * 1.3
		var g := Rect2(c.x - gw * 0.5, c.y - gh * 0.5, gw, gh)
		ci.draw_rect(g, ink, false, 1.0)
		ci.draw_rect(Rect2(g.position.x, g.end.y - gh * 0.3, gw, gh * 0.3), ink)


static func badge_radius(r: float) -> float:
	return maxf(6.0, r * 0.65)


static func badge_centre(p: Vector2, r: float) -> Vector2:
	return p + Vector2(r * 0.95, -r * 0.95)
