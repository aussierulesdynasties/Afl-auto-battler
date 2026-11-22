class_name Tipping
extends RefCounted
## The papers' tipping panel (director, 2026-11-21: "something in every pregame
## that shows the journos tips for the match", on the match preview's team
## comparison; "tips = who they think will win"; "it has to be based on actual
## team form"). The five press-room journalists (MediaConference.JOURNALISTS)
## each tip a winner and a margin for your match.
##
## A tip is worked out from the match's own facts, never a roll: each side's
## strength as picked (Squad.strength, so injuries and omissions count), its
## ladder place and percentage, its last five results (ClubLife.team_form) and
## which side has the home-ground edge the engine plays (Season.round_at_home,
## finals_at_home). Each journalist weighs those facts his own way, so they
## split only when the facts pull different ways: a strong side out of form,
## a weaker side at home. The same facts always give the same tips.
##
## Words only: nothing here reaches the sim, and the panel tips every club's
## matches by the same rule.

## The panel in the order it is printed.
const PANEL := ["stats", "philosopher", "sycophant", "muckraker", "bogan"]

## How much each journalist makes of each fact, in points of margin.
##   strength  per point of Squad.strength between the sides
##   ladder    per ladder place between them, once both have played LADDER_FULL
##   pct       per 10 points of percentage between them, the same
##   form      per unit of ClubLife.team_form between them (each side -1..1)
##   home      for the side with the home-ground edge
## Dev Mehta trusts the ratings and the percentage; Margaret Ashby the list
## itself; Trish Lomax the big names and the home crowd; Gary Haddon only the
## ladder and the results; Kev Pollard the form and the home crowd.
const WEIGHTS := {
	"stats": {"strength": 2.6, "ladder": 1.0, "pct": 3.0, "form": 4.0, "home": 4.0},
	"philosopher": {"strength": 3.2, "ladder": 0.6, "pct": 1.5, "form": 3.0, "home": 4.0},
	"sycophant": {"strength": 2.4, "ladder": 1.2, "pct": 1.0, "form": 6.0, "home": 8.0},
	"muckraker": {"strength": 1.0, "ladder": 2.2, "pct": 2.4, "form": 9.0, "home": 4.0},
	"bogan": {"strength": 1.2, "ladder": 0.8, "pct": 0.6, "form": 12.0, "home": 10.0},
}
## Games each side must have played before the ladder counts in full: after
## one round the ladder says very little.
const LADDER_FULL := 6
## A tip's margin is always at least a point and never silly.
const MAX_MARGIN := 60


## The panel's tips for one match. `home` and `away` are each side's facts:
## {"code", "strength" (Squad.strength), "pos" (ladder place, 1 = top),
## "pct" (percentage), "played" (games this season), "form" (-1..1),
## "edge" (true when it has the home-ground edge)}.
## Returns one row per journalist in PANEL order: {"journalist", "name",
## "outlet", "pick" (club code), "margin" (points, 1+)}.
static func panel(home: Dictionary, away: Dictionary) -> Array:
	var out := []
	for j in PANEL:
		var m := lean(str(j), home, away)
		var pick := str(home["code"]) if m > 0.0 else str(away["code"])
		if is_zero_approx(m):
			# Dead level: a tipster still has to pick, and goes with the side
			# that is better on paper, then the home side.
			pick = str(away["code"]) if float(away["strength"]) > float(home["strength"]) else str(home["code"])
		var who: Dictionary = MediaConference.JOURNALISTS.get(j, {})
		out.append({"journalist": j, "name": str(who.get("name", "")), "outlet": str(who.get("outlet", "")),
				"pick": pick, "margin": clampi(roundi(absf(m)), 1, MAX_MARGIN)})
	return out


## One journalist's lean, in points: above 0 for the home side.
static func lean(journalist: String, home: Dictionary, away: Dictionary) -> float:
	var w: Dictionary = WEIGHTS[journalist]
	var m := float(w["strength"]) * (float(home["strength"]) - float(away["strength"]))
	# The ladder counts as both sides' seasons do: nothing before a game.
	var games := mini(int(home.get("played", 0)), int(away.get("played", 0)))
	var trust := clampf(float(games) / LADDER_FULL, 0.0, 1.0)
	m += trust * float(w["ladder"]) * float(int(away.get("pos", 0)) - int(home.get("pos", 0)))
	m += trust * float(w["pct"]) * (float(home.get("pct", 100.0)) - float(away.get("pct", 100.0))) / 10.0
	m += float(w["form"]) * (float(home.get("form", 0.0)) - float(away.get("form", 0.0)))
	if bool(home.get("edge", false)):
		m += float(w["home"])
	if bool(away.get("edge", false)):
		m -= float(w["home"])
	return m


## How many tip each side: {code: count}, both codes present.
static func tally(tips: Array, home_code: String, away_code: String) -> Dictionary:
	var out := {home_code: 0, away_code: 0}
	for t in tips:
		out[str(t["pick"])] = int(out.get(str(t["pick"]), 0)) + 1
	return out


## The panel's verdict in a line: "All five tip Collingwood." or
## "Three of five tip Carlton." `names`: code -> the name to print.
static func headline(tips: Array, names: Dictionary) -> String:
	if tips.is_empty():
		return ""
	var counts := {}
	for t in tips:
		counts[str(t["pick"])] = int(counts.get(str(t["pick"]), 0)) + 1
	var top := ""
	for c in counts:
		if top == "" or int(counts[c]) > int(counts[top]):
			top = str(c)
	var n := tips.size()
	var club := str(names.get(top, top))
	if int(counts[top]) == n:
		return "All %s tip %s." % [_word(n), club]
	return "%s of %s tip %s." % [_word(int(counts[top])).capitalize(), _word(n), club]


static func _word(n: int) -> String:
	var words := ["none", "one", "two", "three", "four", "five", "six", "seven", "eight"]
	return words[n] if n >= 0 and n < words.size() else str(n)
