class_name Archetypes
extends RefCounted
## The coach's two archetypes (row 119, director 2026-11-10): one Strategic (the
## plan he knows best) and one Philosophical (how he runs the group). Every
## senior coach holds one of each and the effects stack. Pure rules: the
## appointment interview's questions and scoring, the match levers each
## archetype carries, the drift over seasons and a rival coach's archetypes
## from his record. GameState keeps the scores (coach_arch).
##
## Sizes were measured on paired seeds (1,000 matches each, tools/balance.sh
## --arch): every archetype alone and four stacked pairs sit inside the noise.
## Balance stays the director's call.

const STRATEGIC := ["DS", "TA", "CC", "PC"]
const PHILOSOPHICAL := ["HARD", "ANA", "FATH", "GAMB"]

const NAME := {
	"DS": "Defence and System", "TA": "Territory and Attack",
	"CC": "Contest and Clearance", "PC": "Possession and Control",
	"HARD": "Hardline Disciplinarian", "ANA": "Analytical Tactician",
	"FATH": "Father Figure", "GAMB": "The Gambler",
}

## The plan a Strategic archetype knows best (MatchSim.PLANS keys). Its upside
## and its cost grow only while his side plays that plan; on any other plan he
## coaches at plain capacity.
const PLAN := {"DS": "defensive", "TA": "attacking", "CC": "contest", "PC": "controlled"}

## A Strategic archetype's size on his own plan: half a game plan again on top
## of the plan, its upside (sup) and its cost (scost). Territory's cost is
## doubled: at 1.5 it measured +3.8 points a match, outside the noise.
const STRATEGIC_SIZE := {
	"DS": {"sup": 1.5, "scost": 1.5}, "TA": {"sup": 1.5, "scost": 2.0},
	"CC": {"sup": 1.5, "scost": 1.5}, "PC": {"sup": 1.5, "scost": 1.5},
}

## A Philosophical archetype's match levers (MatchSim.arch keys):
##   clangers, fifty (50m penalties and reports given away), legs (how fast
##   they drain), goal (own conversion), exposed (their conversion on the
##   turnover), morale (points of morale, 10 = 1% match fitness), inj (injury
##   risk), exec (game-plan execution).
## Off the match: kids_xp (22 and under), sting (left-out morale loss) and
## swing (a win's lift and a loss's sting).
const LEVERS := {
	"HARD": {"clangers": 0.965, "fifty": 0.85, "legs": 0.98, "morale": -10.0, "inj": 1.12},
	"ANA": {"exec": 1.125, "morale": -10.0},
	"FATH": {"morale": 10.0, "clangers": 1.06, "fifty": 1.20},
	"GAMB": {"goal": 1.025, "exposed": 1.06, "clangers": 1.03},
}
const KIDS_XP := {"FATH": 1.05}
const KIDS_AGE := 22
## Left-out sting: the share of a left-out player's morale loss, as a factor.
const STING := {"HARD": 1.25, "ANA": 1.25, "FATH": 0.75}
## Morale after a result for the Gambler: wins lift more, losses sting more.
const SWING_WIN := 2
const SWING_LOSS := -2

## What each archetype does, in football words (the reveal and the coach sheet).
const UPSIDE := {
	"DS": "On Defensive Press your press bites harder and they kick fewer of their shots.",
	"TA": "On Attack Corridor you kick more of your shots and gain more ground.",
	"CC": "On Win Contest you win more of the stoppages.",
	"PC": "On Controlled Tempo you turn it over less and your legs last longer.",
	"HARD": "Fewer clangers, fewer 50m penalties and reports, and legs that last a little longer.",
	"ANA": "Your game plan is carried out better, whichever plan you run.",
	"FATH": "Higher morale, and kids 22 and under develop a little faster.",
	"GAMB": "You kick more of your shots, and wins lift the group more.",
}
const COST := {
	"DS": "On Defensive Press you kick fewer of your own, gain less ground and burn more legs.",
	"TA": "On Attack Corridor you give away more clangers, burn more legs and leave more open on the turnover.",
	"CC": "On Win Contest you gain less ground and leave more open on the turnover.",
	"PC": "On Controlled Tempo you gain less ground.",
	"HARD": "Lower morale, and a few more injuries.",
	"ANA": "Lower morale, and being left out stings more.",
	"FATH": "More clangers, more 50m penalties and reports.",
	"GAMB": "They score more on the turnover, a few more clangers, and losses sting more.",
}
## On any other plan a Strategic archetype is plain capacity.
const OFF_PLAN := "On any other plan you coach it as written."

## Rival coaches' reports never put an archetype's name on a real coach
## (Coaches.gd): they say what he does (RivalRead.coach_line style).
const RIVAL_LINE := {
	"DS": "his side's press bites harder on Defensive Press, and burns more legs",
	"TA": "his side takes the game on through the corridor, and leaves more open behind it",
	"CC": "his side wins more stoppages on Win Contest, and gains less ground",
	"PC": "his side keeps it on Controlled Tempo with fewer turnovers, and gains less ground",
	"HARD": "runs a hard ship: fewer free kicks and 50s, but his players' morale runs lower",
	"ANA": "his game plans are carried out to the letter, but his players' morale runs lower",
	"FATH": "his players love playing for him, but they give away more free kicks",
	"GAMB": "goes for broke: kicks straighter, leaves more open behind it",
}

## The appointment interview (row 119). Every question is one set: Strategic
## questions weigh 4 + 2 + 4 = 10 per archetype, Philosophical 2 + 3 + 3 + 2.
## Answers are in a fixed order per question; "a" is the archetype it scores.
## "<Name>" and "<Club>" are filled in by the screen.
const QUESTIONS := [
	{"j": "sycophant", "set": "s", "w": 4,
		"q": "<Name>, congrats on your appointment as <Club> senior coach. You beat <Rival> for the job. What sort of footy do you want this club to play?",
		"answers": [["DS", "We'll hunt the ball. Nobody gets an easy kick against us."],
			["TA", "We'll win the territory and take the game on. Some of it will go wrong."],
			["CC", "We win it at the contest first. Everything comes off that."],
			["PC", "We'll keep the ball and make them chase it."]]},
	{"j": "stats", "set": "s", "w": 2,
		"q": "Come draft night, what are you looking for?",
		"answers": [["DS", "Kids who'll chase and defend all day."],
			["TA", "Pace and long kicks. You can't teach either."],
			["CC", "Big-bodied ball winners, ready now."],
			["PC", "Foot skills. Blokes who hit targets."]]},
	{"j": "bogan", "set": "p", "w": 2,
		"q": "Righto, pre-season. You flogging 'em or what?",
		"answers": [["HARD", "Hardest pre-season they've had. That's where games get won."],
			["ANA", "Every session's got a number on it. The GPS tells me when to back off."],
			["FATH", "Load it around each bloke. I'll know who needs what because I'll ask him."],
			["GAMB", "Flog 'em early. If a couple break, a couple break."]]},
	{"j": "muckraker", "set": "p", "w": 3,
		"q": "A young bloke misses a team meeting in game week. Does he play?",
		"answers": [["HARD", "No. Same rule for everyone."],
			["FATH", "I sit down with him first, then I decide."],
			["ANA", "He's picked on his numbers. The meeting's a separate matter."],
			["GAMB", "He plays. If it blows up, I'll wear it."]]},
	{"j": "philosopher", "set": "s", "w": 4,
		"q": "Last ten minutes, up by a goal. What do you want from your players?",
		"answers": [["DS", "Stay on their ball carrier. Make them earn every metre."],
			["TA", "Go and get another. Sitting on a lead loses games."],
			["CC", "Lock it up. Win the next stoppage, and the next."],
			["PC", "Keep it, chip it around, run the clock down."]]},
	{"j": "muckraker", "set": "p", "w": 3,
		"q": "Down three goals at three-quarter time. What do you say in the huddle?",
		"answers": [["HARD", "Not good enough, and I'll tell them."],
			["ANA", "Here's what the numbers say, here's the change."],
			["FATH", "I back them. They know it."],
			["GAMB", "Throw the magnets up and go for broke."]]},
	{"j": "sycophant", "set": "p", "w": 2,
		"q": "Last one. What do you predict for the season to come?",
		"answers": [["HARD", "Finals, or I haven't done my job."],
			["ANA", "We'll be better in the numbers that win games; the ladder follows."],
			["FATH", "Judge us on how the kids grow this year."],
			["GAMB", "We'll win the flag or fall over trying."]]},
]

## Drift: each season every score is multiplied by DECAY, then SHARE points
## are shared by what he actually did that season.
const DECAY := 0.8
const SHARE := 2.5

## Press answer kinds (MediaConference.ANSWERS) and in-match calls
## (MatchSim BURSTS keys) that earn Philosophical points.
const PRESS_KIND := {"back": "FATH", "back_named": "FATH", "criticise": "HARD",
		"criticise_named": "HARD", "method": "ANA"}
const CALL_KEY := {"surge": "GAMB", "stack": "GAMB", "push": "GAMB"}


## An empty record: no scores, nothing held, nothing tallied.
static func blank() -> Dictionary:
	return {"s": {}, "p": {}, "held": {"s": "", "p": ""}, "tally": {"plans": {}, "calls": {}}}


## The interview's scores from `picks` (one answer index per question, in
## order): {"s": {id: points}, "p": {id: points}, "held": {"s": id, "p": id}}.
static func score_interview(picks: Array) -> Dictionary:
	var out := blank()
	var last := {"s": {}, "p": {}}
	for i in range(mini(picks.size(), QUESTIONS.size())):
		var q: Dictionary = QUESTIONS[i]
		var a := int(picks[i])
		if a < 0 or a >= (q["answers"] as Array).size():
			continue
		var id := str(q["answers"][a][0])
		var set_key := str(q["set"])
		out[set_key][id] = float(out[set_key].get(id, 0.0)) + float(q["w"])
		last[set_key][id] = i
	for set_key in ["s", "p"]:
		out["held"][set_key] = _top(out[set_key], last[set_key], "")
	return out


## The highest score; among a tie, the one answered last (`order`: id -> the
## question it was last chosen on), and with no order the one already held.
static func _top(scores: Dictionary, order: Dictionary, held: String) -> String:
	var best := ""
	var best_v := -1.0
	for id in scores:
		var v := float(scores[id])
		if v > best_v + 1e-9:
			best = str(id)
			best_v = v
		elif absf(v - best_v) <= 1e-9:
			if order.is_empty():
				if str(id) == held:
					best = str(id)
			elif int(order.get(id, -1)) > int(order.get(best, -1)):
				best = str(id)
	return best


## One season's drift. `shares`: id -> share of the season (0..1) earned by
## what he did. Returns the new scores.
static func drift(scores: Dictionary, shares: Dictionary) -> Dictionary:
	var out := {}
	for id in scores:
		out[id] = float(scores[id]) * DECAY
	for id in shares:
		out[id] = float(out.get(id, 0.0)) + SHARE * float(shares[id])
	return out


## The archetype held after a season: the top score, the held one keeping a
## tie (a change needs a lead).
static func held_after(scores: Dictionary, held: String) -> String:
	if scores.is_empty():
		return held
	var top := _top(scores, {}, held)
	if held != "" and float(scores.get(top, 0.0)) <= float(scores.get(held, 0.0)) + 1e-9:
		return held
	return top


## Season-end: shares from the tally, drift both sets, and what changed.
## Returns {"arch": the new record (tally cleared), "changed": [[set, from, to]]}.
static func season_end(arch: Dictionary) -> Dictionary:
	var a: Dictionary = arch.duplicate(true) if not arch.is_empty() else blank()
	var tally: Dictionary = a.get("tally", {})
	var plans: Dictionary = tally.get("plans", {})
	var calls: Dictionary = tally.get("calls", {})
	var s_shares := {}
	var games := 0
	for plan in plans:
		games += int(plans[plan])
	for id in PLAN:
		if games > 0:
			s_shares[id] = float(plans.get(PLAN[id], 0)) / float(games)
	var p_shares := {}
	var acts := 0
	for id in calls:
		acts += int(calls[id])
	for id in calls:
		if acts > 0:
			p_shares[id] = float(calls[id]) / float(acts)
	var changed := []
	for pair in [["s", s_shares], ["p", p_shares]]:
		var key: String = pair[0]
		var before := str((a["held"] as Dictionary).get(key, ""))
		a[key] = drift(a.get(key, {}), pair[1])
		var after := held_after(a[key], before)
		a["held"][key] = after
		if after != before:
			changed.append([key, before, after])
	a["tally"] = {"plans": {}, "calls": {}}
	return {"arch": a, "changed": changed}


## A match on `plan` counts toward the Strategic drift.
static func tally_plan(arch: Dictionary, plan: String) -> void:
	_tally(arch, "plans", plan)


## A press answer of `kind` or an in-match call `key` counts toward the
## Philosophical drift (nothing for the rest).
static func tally_press(arch: Dictionary, kind: String) -> void:
	if PRESS_KIND.has(kind):
		_tally(arch, "calls", str(PRESS_KIND[kind]))


static func tally_call(arch: Dictionary, key: String) -> void:
	if CALL_KEY.has(key):
		_tally(arch, "calls", str(CALL_KEY[key]))


static func _tally(arch: Dictionary, bucket: String, key: String) -> void:
	if arch.is_empty():
		for k in blank():
			arch[k] = blank()[k]
	var t: Dictionary = arch["tally"]
	if not t.has(bucket):
		t[bucket] = {}
	t[bucket][key] = int(t[bucket].get(key, 0)) + 1


## The match levers for a coach holding Strategic `s` and Philosophical `p`
## (MatchSim.arch): {} when he holds neither.
static func levers(s: String, p: String) -> Dictionary:
	var out := {}
	if PLAN.has(s):
		out["fplan"] = PLAN[s]
		for k in STRATEGIC_SIZE[s]:
			out[k] = float(STRATEGIC_SIZE[s][k])
	if LEVERS.has(p):
		for k in LEVERS[p]:
			# Multipliers stack by product, morale points by sum.
			if k == "morale":
				out[k] = float(out.get(k, 0.0)) + float(LEVERS[p][k])
			else:
				out[k] = float(out.get(k, 1.0)) * float(LEVERS[p][k])
	return out


## The levers of a held record (GameState.coach_arch).
static func levers_of(arch: Dictionary) -> Dictionary:
	if arch.is_empty():
		return {}
	var held: Dictionary = arch.get("held", {})
	return levers(str(held.get("s", "")), str(held.get("p", "")))


## A rival senior coach's Philosophical archetype from his record (it moves
## with him between clubs): reactive, or balanced and sharp (tactics 78+), is
## Analytical; stubborn is Hardline; cautious, or a balanced man-manager
## (manage 80+), is Father Figure; the gambler is the Gambler. Any other
## balanced coach goes by his stronger of tactics and man-management.
static func rival_philosophical(style: String, skills: Dictionary) -> String:
	var tactics := float(skills.get("tactics", 70))
	var manage := float(skills.get("manage", 70))
	match style:
		"reactive":
			return "ANA"
		"stubborn":
			return "HARD"
		"cautious":
			return "FATH"
		"gambler":
			return "GAMB"
	if tactics >= Coaches.STYLE_SHARP:
		return "ANA"
	if manage >= 80.0:
		return "FATH"
	return "ANA" if tactics >= manage else "FATH"


## A rival club's Strategic archetype from its usual plan ("" for Balanced).
static func strategic_for_plan(plan: String) -> String:
	for id in PLAN:
		if str(PLAN[id]) == plan:
			return str(id)
	return ""


## The season-end line when an archetype changes.
static func change_line(set_key: String, from_id: String, to_id: String) -> String:
	var what := "the plan you know best" if set_key == "s" else "the way you run the group"
	if from_id == "":
		return "Your coaching has a shape now: %s is %s." % [what, NAME.get(to_id, to_id)]
	return "How you coached this year changed %s: %s, no longer %s." % [what, NAME.get(to_id, to_id), NAME.get(from_id, from_id)]
