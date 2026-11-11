class_name PowerRankings
extends RefCounted
## The papers' pre-season power rankings (director, 2026-11-12: "a summary for
## every team like a proper power ranking would be cool"): a line or two on each
## club in a footy writer's voice, built from that club's own facts (its place on
## the paper's ladder and last year's finish, its best players and lines, a
## recruit, a summer injury, a kid to watch, a narrow practice result). Every
## club the same, yours included. Words only: nothing here reaches the sim.
##
## A club's facts (`facts[code]`, all optional except "name" and "star"):
##   name     the club's name                 pos      its place on the paper's ladder
##   last     last year's finish (0 unknown)  star     its best player's name
##   second   its next best player's name     line     {"word", "rank", "lead"} its best line
##   weak     {"word", "rank"} its worst line recruit  {"name", "from"} its best new face
##   hurt     {"name", "kind"} its best player out injured ("a hamstring injury")
##   young    {"name", "age"} the kid to watch  margin  its practice margin (has_margin true)
##   move     the paper's line on its practice move ("" when it did not move)

## Lead sentences, by angle. Every one names a player. {c} club, {s} star,
## {l} line leader, {line} the line, {last} last year's finish, {r} recruit,
## {from} his old club.
const LEADS := {
	"top": [
		"{c} start the year as the side to beat, and {s} is a big reason why.",
		"Hard to look past {c}: {s} leads a list with very few holes.",
		"{c} sit at the head of most tipsters' lists, and {s} gives them a match-winner most clubs would love.",
	],
	"bottom": [
		"It shapes as a long year for {c}, and {s} cannot carry them alone.",
		"{c} are tipped to finish near the bottom; {s} is the one sure thing on the list.",
		"Few give {c} much of a chance, though {s} will keep them honest most weeks.",
	],
	"rise": [
		"{c} finished {last} last year and the paper has them pushing well higher, with {s} driving it.",
		"Expect a big jump from {c} after finishing {last}; {s} is ready to lead it.",
		"From {last} last season, {c} are tipped to climb, and {s} is the main reason.",
	],
	"fall": [
		"{c} finished {last} last year, but the paper reckons a slide is coming and {s} will need help.",
		"Questions hang over {c} after a {last}-place finish, and {s} cannot answer them all.",
		"A drop is tipped for {c} from {last} last year, with too much resting on {s}.",
	],
	"recruit": [
		"{c} have landed {r} from {from}, and the addition will lift them straight away.",
		"All eyes are on {r} at {c} after the move from {from}.",
		"The arrival of {r} from {from} gives {c} a fresh look this year.",
		"{c} went shopping over summer and came home with {r} from {from}.",
	],
	"line_best": [
		"{c} boast the best {line} in the competition, with {l} at the heart of it.",
		"No club can match the {line} {c} roll out, and {l} leads it.",
		"Start with the {line}: {l} heads the deepest one in the league at {c}.",
	],
	"line_top": [
		"The {line} is the strength at {c}, with {l} the pick of a deep group.",
		"Built around {l}, {c} have a {line} as good as any outside the very best.",
		"{l} leads a top-four {line} at {c}.",
		"{c} will lean on a quality {line}, and {l} is its best player.",
	],
	"line_solid": [
		"{c} have a solid {line}, and {l} is the pick of it.",
		"{l} gives {c} a {line} that holds its own most weeks.",
		"There is a sturdy {line} at {c}, led by {l}.",
	],
	"finals": [
		"{c} look a genuine finals side, with {s} the heartbeat.",
		"Finals are the floor for {c}, and {s} is why.",
		"{c} will be playing in September if {s} has another big year.",
	],
	"bubble": [
		"{c} sit on the finals bubble, and {s} could be the difference.",
		"{c} shape as a fringe finals side, with plenty riding on {s}.",
		"Eighth is within reach for {c} if {s} gets enough help.",
	],
	"lower": [
		"{c} have work to do to play finals, though {s} gives them a start.",
		"It is a building year at {c}, with {s} the one to build around.",
		"{c} look short of the top eight, even with {s} in the side.",
	],
	"line_any": [
		"{l} is the pick of the {c} {line}.",
		"The {line} is where {c} look best, led by {l}.",
	],
	"star": [
		"Everything at {c} still runs through {s}.",
		"{s} remains the one player {c} cannot do without.",
		"{c} will go as far as {s} takes them.",
		"If {s} stays fit, {c} will trouble plenty of sides.",
		"{s} is still the first name on the {c} team sheet.",
		"{c} have a genuine star in {s}, and the rest of the list has to catch up.",
		"Opposition coaches will plan for {s} first when they meet {c}.",
		"{c} lean heavily on {s}, and few would blame them.",
	],
}

## Second sentences, by angle, after a lead that left room. {h} injured
## player, {kind} the injury, {m} practice margin, {weak} worst line, {y}
## young player, {age} his age, {s2} the next best player.
const TAILS := {
	"hurt": [
		"Losing {h} to {kind} hurts early.",
		"{h} is out with {kind}, a worry for the early rounds.",
		"Without {h} ({kind}) for the start, the depth will be tested.",
		"{kind} to {h} takes some shine off the start.",
	],
	"won": [
		"A {m}-point practice win was a tidy enough hit-out.",
		"They got through the practice match {m} points up without showing their hand.",
	],
	"lost": [
		"A {m}-point practice loss told us little either way.",
		"The {m}-point practice loss is nothing to panic about.",
	],
	"weak": [
		"The {weak} looks thin, though.",
		"The worry is a {weak} that sits among the league's weakest.",
		"A light {weak} could cost them against the better sides.",
		"Their {weak} needs someone to step up.",
	],
	"young": [
		"Keep an eye on {y}, {age}, who looks ready for more.",
		"{y} is the young one to watch.",
		"At {age}, {y} could be the breakout story.",
		"Watch for {y} to push for a regular spot.",
		"{y}, just {age}, is pushing for senior footy.",
		"The kids are coming too, led by {y}.",
	],
	"second": [
		"{s2} gives them a second weapon.",
		"{s2} is not far behind.",
		"Plenty will rest on {s2} as well.",
		"{s2} will be just as important.",
	],
}


## The blurb for every club in `order` (the paper's ladder, best first), as
## club -> text. No two clubs share a sentence frame; the same facts always
## print the same blurbs.
static func blurbs(order: Array, facts: Dictionary) -> Dictionary:
	var used := {}
	var out := {}
	for code in order:
		var f: Dictionary = facts.get(str(code), {})
		if f.is_empty():
			continue
		out[str(code)] = blurb(str(code), f, used)
	return out


## One club's blurb; `used` holds the frames other clubs already took.
static func blurb(code: String, f: Dictionary, used: Dictionary) -> String:
	var vals := _values(f)
	var lead := ""
	var lead_names: Array = []
	for angle in _lead_angles(f):
		lead = _take(LEADS, angle, code, used, vals)
		if lead != "":
			lead_names = _names_in(angle, vals)
			break
	if lead == "":
		lead = "%s need plenty from %s this year." % [vals["c"], vals["s"]]
	# A club the practice match moved: the paper's own line on it is the second
	# sentence (no other line repeats it).
	var move := str(f.get("move", ""))
	if move != "":
		return "%s %s." % [lead, move]
	for angle in _tail_angles(f, lead_names, vals):
		var tail := _take(TAILS, angle, code, used, vals)
		if tail != "":
			return "%s %s" % [lead, _cap(tail)]
	return lead


static func _values(f: Dictionary) -> Dictionary:
	var line: Dictionary = f.get("line", {})
	var weak: Dictionary = f.get("weak", {})
	var rec: Dictionary = f.get("recruit", {})
	var hurt: Dictionary = f.get("hurt", {})
	var young: Dictionary = f.get("young", {})
	return {
		"c": str(f.get("name", "")), "s": str(f.get("star", "")), "s2": str(f.get("second", "")),
		"l": str(line.get("lead", "")), "line": str(line.get("word", "")),
		"weak": str(weak.get("word", "")),
		"last": ordinal(int(f.get("last", 0))),
		"r": str(rec.get("name", "")), "from": str(rec.get("from", "")),
		"h": str(hurt.get("name", "")), "kind": str(hurt.get("kind", "")),
		"y": str(young.get("name", "")), "age": str(int(young.get("age", 0))),
		"m": str(absi(int(f.get("margin", 0)))),
	}


## The leads that fit a club, the most newsworthy first.
static func _lead_angles(f: Dictionary) -> Array:
	var out := []
	var pos := int(f.get("pos", 0))
	var n := int(f.get("clubs", 18))
	var last := int(f.get("last", 0))
	if pos > 0 and pos <= 2:
		out.append("top")
	if pos > 0 and pos >= n - 1:
		out.append("bottom")
	if last > 0 and pos > 0 and last - pos >= 4:
		out.append("rise")
	if last > 0 and pos > 0 and pos - last >= 4:
		out.append("fall")
	if not (f.get("recruit", {}) as Dictionary).is_empty():
		out.append("recruit")
	var rank := int((f.get("line", {}) as Dictionary).get("rank", 99))
	if rank == 1:
		out.append("line_best")
	if rank <= 4:
		out.append("line_top")
	out.append("star")
	if pos >= 3 and pos <= 8:
		out.append("finals")
	elif pos >= 9 and pos <= 12:
		out.append("bubble")
	elif pos >= 13 and pos < n - 1:
		out.append("lower")
	if rank <= 9:
		out.append("line_solid")
	out.append("line_any")
	return out


## The second sentences that fit, none naming a player the lead already named.
static func _tail_angles(f: Dictionary, named: Array, vals: Dictionary) -> Array:
	var out := []
	if vals["h"] != "" and not named.has(vals["h"]):
		out.append("hurt")
	if bool(f.get("has_margin", false)) and int(f.get("margin", 0)) != 0:
		out.append("won" if int(f["margin"]) > 0 else "lost")
	if int((f.get("weak", {}) as Dictionary).get("rank", 0)) >= int(f.get("clubs", 18)) - 3:
		out.append("weak")
	if vals["y"] != "" and not named.has(vals["y"]):
		out.append("young")
	if vals["s2"] != "" and not named.has(vals["s2"]):
		out.append("second")
	return out


## The players a lead of this angle names.
static func _names_in(angle: String, vals: Dictionary) -> Array:
	match angle:
		"recruit":
			return [vals["r"]]
		"line_best", "line_top", "line_solid", "line_any":
			return [vals["l"]]
	return [vals["s"]]


## The first frame of `angle` no other club has used, starting from this club's
## own place in the list so the same frames don't always go first. "" when
## every frame is taken.
static func _take(pool: Dictionary, angle: String, code: String, used: Dictionary, vals: Dictionary) -> String:
	var frames: Array = pool.get(angle, [])
	if frames.is_empty():
		return ""
	var start := absi(hash(code)) % frames.size()
	for k in range(frames.size()):
		var i := (start + k) % frames.size()
		var key := "%s:%d" % [angle, i]
		if used.has(key):
			continue
		used[key] = true
		return str(frames[i]).format(vals)
	return ""


static func _cap(s: String) -> String:
	return s.left(1).to_upper() + s.substr(1) if s != "" else s


static func ordinal(n: int) -> String:
	var suffix := "th"
	if n % 100 < 11 or n % 100 > 13:
		suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
	return "%d%s" % [n, suffix]
