class_name BreakTalks
extends RefCounted
## Quarter-break talks (director, 2026-11-21): at every break the coach may sit
## down with one player, and at half time he may also address the whole group.
## Each is a roll of two dice: the total, plus the coach's edge, says how it
## lands for the next quarter only. Pure rules; MatchSim rolls and applies.
##
## "Roll a dice to give them a boost for the quarter, once per break; at half
## time a coach's speech which will boost the entire team. Both have a small
## chance of back firing, and their benefits scale with the coach's stats and
## relationships with the players."
##
## The edge is what the coach brings to the talk, added to the dice:
##   man-management  the club's man-manager: yours is your senior assistant (you
##                   have no grades of your own, as with tactics); a rival's is
##                   his senior coach. Fair -1, Good 0, Strong or Elite +1.
##   archetype       a Father Figure lands a sit-down better (+1); a Hardline
##                   Disciplinarian lands the half-time spray better (+1).
##   trust           his opinion of you (Trust.gd): lost -2, wary -1, neutral 0,
##                   trusts +1, close +2. A speech reads the group's average.
##                   Only your own players have an opinion of you; a rival's
##                   players are neutral to their coach.
## Every club gets the same rule: rival coaches sit down with their best player
## at every break and speak at half time.
##
## A double one always backfires, whatever the edge: no talk is safe.

## Bands on the total (dice + edge), highest first: [lowest total, key].
const BANDS := [[12, "big"], [10, "lift"], [7, "small"], [4, "none"], [-99, "backfire"]]
const KEYS := ["big", "lift", "small", "none", "backfire"]
## What each band adds to the player's match fitness for the next quarter
## (MatchSim.fit: about 1.05 fresh, so +0.05 is about 5% on everything he does).
const SIT_LIFT := {"big": 0.08, "lift": 0.05, "small": 0.03, "none": 0.0, "backfire": -0.05}
## The speech reaches everyone, so each man's share is smaller than a sit-down.
const SPEECH_LIFT := {"big": 0.03, "lift": 0.02, "small": 0.01, "none": 0.0, "backfire": -0.02}
const EDGE_MIN := -3
const EDGE_MAX := 3
const MANAGE_FAIR := 68.0      # Coaches.GRADES: under 68 is Fair
const MANAGE_STRONG := 78.0    # 78 and up is Strong (or Elite)
const TRUST_EDGE := {"lost": -2, "wary": -1, "neutral": 0, "trusts": 1, "close": 2}
const ARCH_EDGE := {"sit": {"FATH": 1}, "speech": {"HARD": 1}}
## A fit lift as the share of his game it moves (fit is about 1.05 fresh).
const FIT_FRESH := 1.05


static func manage_edge(manage: float) -> int:
	if manage < MANAGE_FAIR:
		return -1
	return 1 if manage >= MANAGE_STRONG else 0


static func trust_edge(t: int) -> int:
	return int(TRUST_EDGE.get(Trust.band(t), 0))


static func arch_edge(kind: String, arch_p: String) -> int:
	return int((ARCH_EDGE.get(kind, {}) as Dictionary).get(arch_p, 0))


## The whole edge for one talk: kind "sit" or "speech".
static func edge(kind: String, manage: float, arch_p: String, t: int) -> int:
	return clampi(manage_edge(manage) + arch_edge(kind, arch_p) + trust_edge(t), EDGE_MIN, EDGE_MAX)


static func band(dice: Array, e: int) -> String:
	# Snake eyes: no edge saves it.
	if int(dice[0]) == 1 and int(dice[1]) == 1:
		return "backfire"
	var total := int(dice[0]) + int(dice[1]) + e
	for b in BANDS:
		if total >= int(b[0]):
			return str(b[1])
	return "backfire"


static func lift(kind: String, key: String) -> float:
	return float((SIT_LIFT if kind == "sit" else SPEECH_LIFT).get(key, 0.0))


## The odds of each band for an edge: {key: share 0..1}, over all 36 rolls.
static func odds(e: int) -> Dictionary:
	var out := {}
	for k in KEYS:
		out[k] = 0.0
	for a in range(1, 7):
		for b in range(1, 7):
			var k := band([a, b], e)
			out[k] = float(out[k]) + 1.0 / 36.0
	return out


## What a lift is worth, as the share of his game: "+5%".
static func size_pct(kind: String, key: String) -> int:
	return roundi(lift(kind, key) / FIT_FRESH * 100.0)


static func _pc(share: float) -> String:
	return "%d%%" % roundi(share * 100.0)


## The gate (bible principle 4: the upside, the downside, the size and the
## odds, in football words; never which is better). [gain, cost] for GateOdds.
static func gate_texts(kind: String, e: int, who := "") -> Array:
	var o := odds(e)
	var up := float(o["small"]) + float(o["lift"]) + float(o["big"])
	var lo := "+%d%%" % size_pct(kind, "small")
	var hi := "+%d%%" % size_pct(kind, "big")
	var down := absi(size_pct(kind, "backfire"))
	if kind == "speech":
		return ["%s odds we lift for the quarter\nThe lift: %s to %s on all of us" % [_pc(up), lo, hi],
				"%s odds it backfires\nOur whole side then plays %d%% below itself" % [_pc(float(o["backfire"])), down]]
	var name := who if who != "" else "He"
	return ["%s odds %s lifts for the quarter\nThe lift: %s to %s on his game" % [_pc(up), name, lo, hi],
			"%s odds it backfires\nHe then plays %d%% below himself" % [_pc(float(o["backfire"])), down]]


## Where the edge comes from, in words: "Edge +2: his opinion of you, 76 out of 100".
static func edge_lines(kind: String, manage: float, arch_p: String, t: int) -> Array:
	var out: Array = []
	var m := manage_edge(manage)
	var grade := Coaches.grade(manage)
	out.append("Our senior assistant, a %s man-manager: %s" % [grade, "%+d" % m if m != 0 else "no edge"])
	var a := arch_edge(kind, arch_p)
	if a != 0:
		out.append("You are a %s: %+d" % [str(Archetypes.NAME.get(arch_p, arch_p)), a])
	var tr := trust_edge(t)
	var op := Trust.opinion(t)
	if kind == "sit":
		out.append("His opinion of you, %d out of 100: %s" % [op, "%+d" % tr if tr != 0 else "no edge"])
	else:
		out.append("The group's opinion of you, %d out of 100: %s" % [op, "%+d" % tr if tr != 0 else "no edge"])
	return out


## What the roll did, in the coach's words. `who` is the player's name for a sit-down.
static func result_line(kind: String, key: String, who := "") -> String:
	var pct := absi(size_pct(kind, key))
	if kind == "sit":
		match key:
			"big":
				return "%s walked out ten feet tall: +%d%% this quarter." % [who, pct]
			"lift":
				return "%s is up for it: +%d%% this quarter." % [who, pct]
			"small":
				return "%s took it on board: +%d%% this quarter." % [who, pct]
			"none":
				return "%s nodded along. No change." % who
			"backfire":
				return "%s took it the wrong way: -%d%% this quarter." % [who, pct]
	match key:
		"big":
			return "The rooms erupted: we all play +%d%% this quarter." % pct
		"lift":
			return "They're fired up: we all play +%d%% this quarter." % pct
		"small":
			return "It landed: we all play +%d%% this quarter." % pct
		"none":
			return "Heads down, nothing stirred. No change."
		"backfire":
			return "It fell flat: we all play -%d%% this quarter." % pct
	return ""
