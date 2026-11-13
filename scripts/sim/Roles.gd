class_name Roles
extends RefCounted
## A footballer's job on match day, beyond his position. Deliberately small:
## only jobs the match engine actually rewards.
##
##  - Wing (position MID). Two of the five midfield spots are the wings. A
##    wing is not at the stoppage: the engine counts contested ball only from
##    the three centre-square midfielders, and on the wing a player gets more
##    of the ball in transition, where his carry and disposal gain the ground.
##    So a natural wing - a runner who uses it - beats a better-rated inside
##    midfielder out there, and a ball-winner is wasted on the wing.
##  - Tagger (position MID, a stopper: pressure well ahead of his own
##    ball-winning). When you tag an opponent in
##    the coach box, a tagger on the ground takes more of the ball off him.
##  - Everyone else keeps the identity his attributes give him (inside
##    midfielder, key forward, ...), from the same vocabulary Training uses.

const WING_SLOTS := 2
## A MID whose running game outweighs his ball-winning by this much (both
## as a share of 2026 midfielders) reads as a wing.
const WING_MARGIN := 0.12
## ...or a MID who wins fewer clearances than this a game, with less than this
## share of his ball contested (on a season of at least WING_STAT_GAMES).
const WING_CLEARANCES := 2.0
const WING_CONTESTED_SHARE := 0.42
const WING_STAT_GAMES := 6.0
## ...but never a midfielder who is one of the league's ball-winners: this many
## clearances or contested possessions a game (season of WING_STAT_GAMES or
## more) makes him an inside midfielder however much he runs (Gulden,
## Callaghan, Holmes, Dawson, Merrett read as wings on percentile gaps).
const WING_NEVER_CLEARANCES := 3.5
const WING_NEVER_CONTESTED := 8.0
## How much more of the transition ball a wing gets, and how much less of
## the stoppage ball (MatchSim.pick_carrier / _stoppage).
const WING_TRANSITION := 1.6
const WING_STOPPAGE := 0.4
## The tagged player's chance to carry the ball, as a multiplier, on fresh legs
## (tag_keep; row 120).
## A Tagger holds him to TAG_WITH_TAGGER. Anyone else does a real but lesser
## job, from his own Pressure: TAG_LOOSEST for the lowest-pressure midfielder up
## to TAG_TIGHTEST_PLAIN for the highest, so the median man is about 58%.
const TAG_WITH_TAGGER := 0.42
const TAG_LOOSEST := 0.66
const TAG_TIGHTEST_PLAIN := 0.50
## What a tagger's legs add to that, all of it on empty: 0.13 x (1 - legs / 100).
const TAG_TIRED := 0.13
## Those are multipliers on his chance to be picked as the carrier, not his
## disposals: the rest of his side's ball still finds him. What a tag does to his
## touches, measured (tools/audit/tag_keep_impl.gd: their biggest midfielder
## tagged from the first bounce v the same man untagged, 2,000 paired matches an
## arm on main 8757ee4a, audit runs 42686692074 (no tag) and 42686698853 to
## 42686727963 (each multiplier held); a real tag (42686736080, 42686741689,
## 42686748555: his legs and all) came within 0.1 of a disposal of it). The card says it in counts (director, 2026-11-10).
## His disposals untagged, a match:
const TAG_USUAL_TOUCHES := 26.83
## [multiplier, his disposals tagged]; read between the rows (touches_at).
const TAG_TOUCHES := [[0.42, 19.48], [0.50, 21.03], [0.58, 22.37], [0.66, 23.53], [0.79, 25.07], [1.0, 26.83]]
## That was one man, their busiest. The card names the man tagged, so it says his
## own touches (row 178, director 2026-11-12: "says 27 touches 100% of the time").
## Measured on main 5b3ba1b5 with tools/audit/tag_usual_impl.gd (balance_body's
## seeds): his touches untagged, from the ratings the carry pick reads
## (MatchSim.pick_carrier: Disposal, Carry, and a wing's share of the running ball),
## fitted over 1,032 midfielder-matches (89 men);
## [constant, per Disposal, per Carry, on a wing]:
const USUAL_TOUCHES_FIT := [1.84, 0.168, 0.116, 1.29]
const USUAL_TOUCHES_MIN := 8.0
## and what a tag takes off him: about the same count of touches whoever he is,
## not the same share (400 paired matches an arm, a different midfielder tagged
## each match, the multiplier held at 0.42 and at 0.66: a midfielder lost 1.09
## times what the busiest man lost at that hold, a wing 1.26 times, his running
## ball being the ball the tag takes).
const TAG_LOSS_INSIDE := 1.09
const TAG_LOSS_WING := 1.26
## A tag never takes more than this share of a quiet man's touches.
const TAG_KEEP_FLOOR := 0.4
## A tagger's pressure, as a share of 2026 midfielders, and how far it must
## outrun his contested ball.
const TAGGER_PRESSURE := 0.70
const TAGGER_MARGIN := 0.20


## What the wing rewards: carry and disposal. Raw attribute blend.
static func wing_fit(p: Dictionary) -> float:
	var a: Dictionary = p.get("attr", {})
	return 0.55 * float(a.get("carry", 0)) + 0.45 * float(a.get("disposal", 0))


## What the centre square rewards: contested ball first.
static func centre_fit(p: Dictionary) -> float:
	var a: Dictionary = p.get("attr", {})
	return 0.75 * float(a.get("contested", 0)) + 0.25 * float(a.get("disposal", 0))


static func is_mid(p: Dictionary) -> bool:
	return str(p.get("role", "")) == "MID" or Traits.plays(p, "MID")


## A natural wing: a midfielder whose running game (against other 2026
## midfielders) clearly outweighs his ball-winning.
static func is_wing(p: Dictionary) -> bool:
	if not is_mid(p) or str(p.get("role", "")) == "RUCK":
		return false
	if float(p.get("gm", 0.0)) >= WING_STAT_GAMES:
		var gms := float(p["gm"])
		if float(p.get("cl", 0.0)) / gms >= WING_NEVER_CLEARANCES 				or float(p.get("cp", 0.0)) / gms >= WING_NEVER_CONTESTED:
			return false
	var mid_view := p.duplicate()
	mid_view["role"] = "MID"
	var run := 0.5 * (PlayerProfile.percentile(mid_view, "carry", true) + PlayerProfile.percentile(mid_view, "disposal", true))
	var win := PlayerProfile.percentile(mid_view, "contested", true)
	if run - win >= WING_MARGIN:
		return true
	# A midfielder who seldom wins it at the stoppage and gets most of his
	# ball on the outside plays on the wing, however modest his volume.
	if str(p.get("role", "")) != "MID" or float(p.get("gm", 0.0)) < WING_STAT_GAMES:
		return false
	var games := float(p["gm"])
	return float(p.get("cl", 0.0)) / games < WING_CLEARANCES \
			and float(p.get("cp", 0.0)) / maxf(1.0, float(p.get("di", 0.0))) < WING_CONTESTED_SHARE


## A tagger: a midfielder whose game is stopping others - elite pressure
## that clearly outweighs both his ball-winning and his running. A star
## ball-winner who can also tackle is an inside midfielder, not a tagger.
static func is_tagger(p: Dictionary) -> bool:
	if str(p.get("role", "")) != "MID" or not p.has("attr"):
		return false
	var mid_view := p.duplicate()
	mid_view["role"] = "MID"
	var press := PlayerProfile.percentile(mid_view, "pressure", true)
	var win := PlayerProfile.percentile(mid_view, "contested", true)
	var run := 0.5 * (PlayerProfile.percentile(mid_view, "carry", true) + PlayerProfile.percentile(mid_view, "disposal", true))
	return press >= TAGGER_PRESSURE and press - maxf(win, run) >= TAGGER_MARGIN


## The multiplier on his chance to carry the ball with `p` tagging him at `legs` (energy out
## of 100; director, 2026-10-11: it comes from the tagger's Pressure and his
## legs). Every tagger takes something off him, and a Tagger the most (row 120).
static func tag_keep(p: Dictionary, legs: float) -> float:
	var fresh := TAG_LOOSEST
	if not p.is_empty() and p.has("attr"):
		if is_tagger(p):
			fresh = TAG_WITH_TAGGER
		else:
			var mid_view := p.duplicate()
			mid_view["role"] = "MID"
			fresh = lerpf(TAG_LOOSEST, TAG_TIGHTEST_PLAIN, PlayerProfile.percentile(mid_view, "pressure", true))
	return fresh + TAG_TIRED * (1.0 - clampf(legs / 100.0, 0.0, 1.0))


## `target`'s disposals a match with nobody on him (USUAL_TOUCHES_FIT); the
## measured man's (TAG_USUAL_TOUCHES) when there is no one named.
static func usual_touches(target: Dictionary) -> float:
	if target.is_empty() or not target.has("attr"):
		return TAG_USUAL_TOUCHES
	var a: Dictionary = target["attr"]
	var f: Array = USUAL_TOUCHES_FIT
	var n := float(f[0]) + float(f[1]) * float(a.get("disposal", 0)) + float(f[2]) * float(a.get("carry", 0))
	if on_wing(target):
		n += float(f[3])
	return maxf(USUAL_TOUCHES_MIN, n)


## `target`'s disposals in a match with `p` tagging him at `legs` (rows 120, 178):
## his usual touches less what tag_keep's multiplier took off the measured man
## (TAG_TOUCHES), sized for a wing or an inside man. No `target`: the measured man.
static func tag_touches(p: Dictionary, legs: float, target: Dictionary = {}) -> float:
	var measured := touches_at(tag_keep(p, legs))
	if target.is_empty() or not target.has("attr"):
		return measured
	var usual := usual_touches(target)
	var loss := (TAG_USUAL_TOUCHES - measured) * (TAG_LOSS_WING if on_wing(target) else TAG_LOSS_INSIDE)
	return maxf(usual * TAG_KEEP_FLOOR, usual - loss)


static func touches_at(multiplier: float) -> float:
	var rows: Array = TAG_TOUCHES
	if multiplier <= float(rows[0][0]):
		return float(rows[0][1])
	for i in range(1, rows.size()):
		var lo: Array = rows[i - 1]
		var hi: Array = rows[i]
		if multiplier <= float(hi[0]):
			return lerpf(float(lo[1]), float(hi[1]), (multiplier - float(lo[0])) / (float(hi[0]) - float(lo[0])))
	return float(rows[rows.size() - 1][1])


## His football identity in two or three words: "Wing", "Tagger",
## "Inside midfielder", "Key forward", "Ruck"...
static func label(p: Dictionary) -> String:
	if p.is_empty() or not p.has("attr"):
		return ""
	var role := str(p.get("role", ""))
	if role == "MID":
		if is_tagger(p):
			return "Tagger"
		if is_wing(p):
			return "Wing"
		return "Inside midfielder"
	return PlayerProfile.player_type(p)


## The key posts of a line (director, 2026-11-07: "Small defenders placed in
## key defender spots"). A line is laid out in spot order (TeamBuilder.SPOTS,
## FormationView.ASSIGN, MatchDirector.SLOTS): index 0 is the goal-square
## post (full-back, full-forward), index SECOND_POST the centre half post
## (centre half-back, centre half-forward), the four between are the flanks
## and pockets. The rule: the line's key position players - a Key defender or
## Key forward as the sim reads him in this line (Matchups) - take the posts,
## the better rated at the goal square. A line short of key players fills a
## post with the tallest of the rest (then the better rated). A line too short
## to have the centre half post (under six) has only the goal-square post.
## Everyone else keeps the order he came in. Only the auto-pick lays a line
## out this way; a coach's own placement is never re-shuffled.
const SECOND_POST := 5


static func key_post_order(players: Array, line: String) -> Array:
	if players.is_empty() or not (line in ["DEF", "FWD"]):
		return players.duplicate()
	var posts_n := 2 if players.size() > SECOND_POST else 1
	# One read per player (player_type is not free), then a plain sort.
	var rank := []
	for i in range(players.size()):
		var p: Dictionary = players[i]
		rank.append([i, is_key_post(p, line), float(p.get("height_cm", 0.0)), int(p.get("overall", 0))])
	rank.sort_custom(func(a, b):
		if a[1] != b[1]:
			return a[1]
		if not a[1] and not is_equal_approx(a[2], b[2]):
			return a[2] > b[2]
		if a[3] != b[3]:
			return a[3] > b[3]
		return a[0] < b[0])
	var post_at := []
	for k in range(posts_n):
		post_at.append(int(rank[k][0]))
	var rest: Array = []
	for i in range(players.size()):
		if not post_at.has(i):
			rest.append(players[i])
	# Goal-square post, then the flanks and pockets, then (in a full line) the
	# centre half post at SECOND_POST; anyone past six follows.
	var out: Array = [players[post_at[0]]]
	if posts_n == 1:
		out.append_array(rest)
		return out
	out.append_array(rest.slice(0, SECOND_POST - 1))
	out.append(players[post_at[1]])
	out.append_array(rest.slice(SECOND_POST - 1))
	return out


## A key position player in this line, read the way the match reads him
## when he is fielded there (Matchups.is_key_defender / is_key_forward on
## his match-day copy, whose role is the line he plays).
static func is_key_post(p: Dictionary, line: String) -> bool:
	var view := p.duplicate()
	view["role"] = line
	if line == "FWD":
		return Matchups.is_key_forward(view)
	return line == "DEF" and Matchups.is_key_defender(view)


## Which of the midfielders on the ground play the wings: the named ones
## first, then the best runners among the rest. Marks copy["line"] = "WING"
## on the slot copies (never the list player). `ground` holds slot copies.
static func mark_wings(ground: Array, named: Array = []) -> void:
	var mids := []
	for p in ground:
		if str(p.get("role", "")) == "MID":
			p.erase("line")
			mids.append(p)
	var wings := []
	for p in mids:
		if named.has(str(p["id"])) and wings.size() < WING_SLOTS:
			wings.append(p)
	var rest := []
	for p in mids:
		if not wings.has(p):
			rest.append(p)
	# The rest: whoever the stoppage misses least, so a star ball-winner is
	# never parked on a wing; among equals, the better runner.
	rest.sort_custom(func(a, b):
		var ca := centre_fit(a)
		var cb := centre_fit(b)
		if not is_equal_approx(ca, cb):
			return ca < cb
		if not is_equal_approx(wing_fit(a), wing_fit(b)):
			return wing_fit(a) > wing_fit(b)
		return str(a["id"]) < str(b["id"]))
	for p in rest:
		if wings.size() >= WING_SLOTS or mids.size() - wings.size() <= 1:
			break
		wings.append(p)
	for p in wings:
		p["line"] = "WING"


static func on_wing(p: Dictionary) -> bool:
	return str(p.get("line", "")) == "WING"


## A fact for the Selection row, or "": a player named on a wing who is
## not a natural one. (A natural wing named in the centre square already
## reads "Wing" - no advice either way.)
static func fit_note(p: Dictionary, slot: String) -> String:
	if slot == "WING" and not is_wing(p):
		return "Not a natural wing"
	return ""
