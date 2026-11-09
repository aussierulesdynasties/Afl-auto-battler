class_name RivalRead
extends RefCounted
## The rival coach read (director, 2026-11-08): what the Assistant's report
## and the break sheet say about the opposition coach, his box and his list.
## Every line comes from the same constants and rules his calls do
## (MatchSim.ai_tactics, ai_mood, COACH_STYLES, tag_quarter, COUNTER;
## PlanFit; PreSeason), so the words cannot drift from what he does.
## Football words only: never a number behind a call, never which plan beats
## theirs, never his next plan as a certainty. Pure: no state, no dice.

## The break before quarter q: the moment a call made "from quarter q" starts.
const BREAKS := {2: "quarter time", 3: "half time", 4: "three-quarter time"}
## When a call made from quarter q can come, said of the rest of the match.
const PERIODS := {1: "at any stage", 2: "after quarter time", 3: "in the second half",
		4: "in the last quarter"}
## "since ..." for a run that started in quarter q.
const SINCE := {1: "all game", 2: "since quarter time", 3: "since half time",
		4: "since three-quarter time"}
const QUARTER_WORDS := ["first", "second", "third", "last"]
## Plans in the order the copy breaks ties.
const ORDER := ["balanced", "attacking", "defensive", "contest", "controlled"]
## A box this sharp or better reacts at the usual pace: the Good coaching cut.
const BOX_USUAL_READ := -0.1
## Matches a club must have played before its season record is read.
const SEASON_MIN := 2
## The pep talks by tactics key (MatchSim._pep_mult), and the words for the
## ones that cost legs, in the legs reason.
const PEPS := {"calm": MatchSim.PEP_CALM, "fire_up": MatchSim.PEP_FIRE, "heat": MatchSim.PEP_HEAT}
const PEP_WORDS := {"fire_up": "been fired up", "heat": "brought the heat"}
## The break read (ai_mood), said as their mood and never their plan.
const MOODS := {
	"protect": "In front like this, they'll be comfortable.",
	"chase": "Behind like this, they'll be chasing.",
	"lost_q": "They're behind and they've lost the quarter: they'll be chasing.",
}


# ---------------------------------------------------------------------------
# Their coach
# ---------------------------------------------------------------------------
## His habit with the scoreboard, from how his tendency (COACH_STYLES) moves
## the plain rule ("balanced"): "goes by the scoreboard: ...".
static func habit(style: String) -> String:
	var base: Dictionary = MatchSim.COACH_STYLES["balanced"]
	var st: Dictionary = MatchSim.COACH_STYLES.get(style, base)
	var p := signf(float(st["protect"]) - float(base["protect"]))
	var c := signf(float(st["chase"]) - float(base["chase"]))
	if p == 0.0 and c == 0.0:
		return "goes by the scoreboard: he shuts up shop when well in front and chases when well behind"
	if p > 0.0 and c > 0.0:
		return "backs his structure: the scoreboard has to swing further than most before he shuts up shop or chases"
	if p < 0.0 and c < 0.0:
		return "throws the magnets around: he shuts up shop or chases on a smaller swing of the scoreboard than most"
	var bits := []
	if p != 0.0:
		bits.append("shuts up shop %s than most when in front" % ("sooner" if p < 0.0 else "later"))
	if c != 0.0:
		bits.append("chases %s than most when behind" % ("sooner" if c < 0.0 else "later"))
	var lead := ""
	if p == 0.0:
		lead = "goes for broke: " if c < 0.0 else "hangs on: "
	elif c == 0.0:
		lead = "sits on a lead: " if p < 0.0 else "lets a lead ride: "
	return lead + "he " + " and ".join(bits)


## When he fires them up (fire_at, fire_q against the plain rule).
static func fire_clause(style: String) -> String:
	var base: Dictionary = MatchSim.COACH_STYLES["balanced"]
	var st: Dictionary = MatchSim.COACH_STYLES.get(style, base)
	var when := str(PERIODS.get(int(st["fire_q"]), "late"))
	var d := float(st["fire_at"]) - float(base["fire_at"])
	if d > 0.0:
		return "He fires them up sooner than most when they're behind %s." % when
	if d < 0.0:
		return "He waits longer than most to fire them up when they're behind %s." % when
	return "He fires them up when they're well behind %s." % when


## "Craig McRae goes by the scoreboard: ... He fires them up ...". `name`
## is his name, or "" for none (said "Their coach").
static func coach_line(name: String, style: String) -> String:
	return "%s %s. %s" % [name if name != "" else "Their coach", habit(style), fire_clause(style)]


## How sharply his box reads the game (Squad.tactics_read: a sharper box is
## moved by a smaller margin, react_margin), and, with a specialist tagger in
## their side, from which break the tag comes.
static func box_line(read: float, tagger: bool) -> String:
	var s := "Their box is steady rather than sharp and slower to react."
	if read >= MatchSim.TAG_SHARP_READ:
		s = "Their box reads the game quickly and reacts early."
	elif read >= BOX_USUAL_READ:
		s = "Their box reacts at about the usual pace."
	if tagger:
		var q := MatchSim.tag_quarter(read)
		s += (" Their tagger goes to work from %s." if q <= MatchSim.TAG_Q_SHARP
				else " Their tagger waits until %s.") % str(BREAKS.get(q, "late"))
	return s


## The counter rule (MatchSim._counter_plan), once: from when he answers
## your plan, and the two things that stop him (his side playing the answer
## much worse, COUNTER_GIVE; the scoreboard, whose mood ai_tactics reads
## first). A plan nothing beats (no COUNTER entry) gets no answer.
static func counter_line() -> String:
	return ("From %s he answers your last quarter's plan with the one that beats it,"
			+ " if his side can play it nearly as well, unless the scoreboard forces his hand.") % \
			str(BREAKS.get(MatchSim.COUNTER_Q, "quarter time"))


# ---------------------------------------------------------------------------
# Their list
# ---------------------------------------------------------------------------
## Which plan the side they would field this week suits most and least
## (PlanFit.edge), or that none stands out (no edge reaches
## PlanFit.STANDING_EDGE). It is this week's side, not their usual game: a
## coach keeps his plan all season (GameState._settle_usual_plans) while his
## side changes, so the line says "this week's side".
static func fit_line(ground: Array) -> String:
	var best := ""
	var worst := ""
	var hi := -INF
	var lo := INF
	for plan in ORDER:
		if not PlanFit.NEEDS.has(plan):
			continue
		var e := PlanFit.edge(ground, plan)
		if e > hi:
			hi = e
			best = plan
		if e < lo:
			lo = e
			worst = plan
	if best == "" or hi < PlanFit.STANDING_EDGE:
		return "This week's side suits no plan over the others."
	return "This week's side suits %s best and %s least." % [called(best), called(worst)]


## How well they know each plan (`levels`: plan -> PreSeason level), in the
## words of your own plan fluency: only the plans below well are named.
static func know_line(levels: Dictionary) -> String:
	var partly := []
	var barely := []
	var well := 0
	for plan in PreSeason.DRILL_PLANS:
		var l := PreSeason.clamp_level(int(levels.get(plan, PreSeason.WELL)))
		if l >= PreSeason.WELL:
			well += 1
		elif l == PreSeason.WELL - 1:
			partly.append(CoachReport.plan_label(str(plan)))
		else:
			barely.append(CoachReport.plan_label(str(plan)))
	if partly.is_empty() and barely.is_empty():
		return "They know every plan well."
	var bits := []
	if not partly.is_empty():
		bits.append("%s only %s" % [_list(partly, "and"), PreSeason.level_word(PreSeason.WELL - 1)])
	if not barely.is_empty():
		bits.append("%s %s" % [_list(barely, "and"), PreSeason.level_word(0)])
	return "They know %s.%s" % [" and ".join(bits), " The rest they know well." if well > 0 else ""]


## What a plan does to their legs (MatchSim.PLANS pace): "" when nothing.
static func legs_clause(plan: String) -> String:
	var pace := _pace(plan)
	if pace > 1.0:
		return "It costs them legs."
	if pace < 1.0:
		return "It saves their legs."
	return ""


# ---------------------------------------------------------------------------
# Who matters
# ---------------------------------------------------------------------------
## Their specialist tagger (MatchSim.tagger_for, Roles.is_tagger) and his job
## (ai_tactics: the most influential of your midfielders on the ground).
static func tagger_line(name: String) -> String:
	return "%s is a tagger: he goes to whichever of your midfielders is doing the most damage." % name


## Their loose man (MatchSim.loose_pick) and when he is put back on a man
## (_ai_interceptor: chasing late, by his coach's tendency).
static func loose_line(name: String, style: String) -> String:
	var st: Dictionary = MatchSim.COACH_STYLES.get(style, MatchSim.COACH_STYLES["balanced"])
	return "%s can roam behind the ball and attack aerial entries; if they're well behind %s, they put him back on a man." % [
			name, str(PERIODS.get(int(st["loose_q"]), "late"))]


## The minder (ai_tactics: a forward sent to a loose man who keeps winning
## the ball in the air, LOOSE_MINDER_WINS): `name` is the forward they would
## send today (Matchups.minder_candidates); the pick is made during the match,
## so it is said as a read.
static func minder_line(name: String) -> String:
	return "If your loose man keeps cutting off their entries, %s is the forward they'd likely send to stand him." % name


# ---------------------------------------------------------------------------
# The break
# ---------------------------------------------------------------------------
## "They played X." for the quarter just played; with `answered` (your plan
## the quarter before, which they countered: ai_why "counter") it says so.
static func played_line(plan: String, answered := "", answered_q := 0) -> String:
	var s := "They played %s" % phrase(plan)
	if answered != "":
		s += ", their answer to your %s %s" % [phrase(answered), in_quarter(answered_q)]
	return s + "."


## Their mood going into the next quarter (MatchSim.ai_mood): "" when the
## scoreboard is not driving them.
static func mood_tail(mood: String) -> String:
	return str(MOODS.get(mood, ""))


## The break sheet's line on the side across from `me`, for the quarter just
## played: what they played, their answer to your plan when that is why they
## played it (ai_why "counter"), and at quarter, half and three-quarter time
## a rival coach's mood for the next quarter when the scoreboard is driving
## him (ai_mood, the rule his next call uses). Never his next plan. "" before
## the first bounce.
static func break_line(sim: MatchSim, me: int) -> String:
	var hist: Array = sim.tactics_history
	if hist.is_empty():
		return ""
	var opp := 1 - me
	var last: Dictionary = hist[hist.size() - 1]
	var answered := ""
	var answered_q := 0
	var why: Array = last.get("why", [])
	if hist.size() >= 2 and why.size() == 2 and str(why[opp]) == "counter":
		var before: Dictionary = hist[hist.size() - 2]
		answered = str(((before["plans"] as Array)[me] as Dictionary).get("gameplan", "balanced"))
		answered_q = int(before.get("quarter", hist.size() - 1))
	var s := played_line(str(((last["plans"] as Array)[opp] as Dictionary).get("gameplan", "balanced")),
			answered, answered_q)
	if (sim.squads[opp] as Squad).ai_plans and sim.current_quarter >= 2 and sim.current_quarter <= 4:
		var m := sim.ai_mood(opp)
		if m != "lost_q" or well_behind(sim, opp):
			var mood := mood_tail(m)
			if mood != "":
				s += " " + mood
	return s


## Whether `side` is well behind: the margin the game already calls that, its
## coach's fire-up mark (COACH_STYLES fire_at: 12 points, a gambler 9). A side
## that has lost the quarter but is closer than this gets no chasing line, on
## the director's ruling of 2026-11-09; his call itself does not change.
static func well_behind(sim: MatchSim, side: int) -> bool:
	var style := str((sim.squads[side] as Squad).coach_style)
	var st: Dictionary = MatchSim.COACH_STYLES.get(style, MatchSim.COACH_STYLES["balanced"])
	return float(sim.score(side) - sim.score(1 - side)) <= float(st["fire_at"])


## One side's calls in each quarter played so far (tactics_history): its
## tactics, {"gameplan", "pep", ...}, one per quarter in order.
static func calls_of(sim: MatchSim, side: int) -> Array:
	var out := []
	for h in sim.tactics_history:
		out.append(((h["plans"] as Array)[side] as Dictionary).duplicate())
	return out


## Why their legs are going, from both sides' calls so far (calls_of). Said
## only when their calls are the cause: the last quarter's plan and pep talk
## cost them legs (MatchSim.PLANS and PEP_* pace), and their calls have cost
## more than yours over the game. It names the run of plans that cost legs
## and the run of fire-ups that end with the last quarter: "they've pressed
## since quarter time and been fired up since half time". "" otherwise.
static func legs_reason(theirs: Array, mine: Array) -> String:
	var n := theirs.size()
	if n == 0 or _cost(theirs[n - 1]) <= 1.0:
		return ""
	var spent := 0.0
	for i in range(n):
		spent += _cost(theirs[i]) - (_cost(mine[i]) if i < mine.size() else 1.0)
	if spent <= 0.0:
		return ""
	var bits := []
	var start := _run_start(theirs, func(c): return _pace(_plan(c)) > 1.0)
	if start >= 0:
		var run := {}
		for i in range(start, n):
			run[MatchSim.plan_key(_plan(theirs[i]))] = true
		var verb := "run hard"
		if run.size() == 1 and run.has("defensive"):
			verb = "pressed"
		elif run.size() == 1 and run.has("attacking"):
			verb = "run it through the corridor"
		bits.append("%s %s" % [verb, str(SINCE.get(start + 1, "late"))])
	var pep := _pep(theirs[n - 1])
	if PEP_WORDS.has(pep):
		var since := _run_start(theirs, func(c): return _pep(c) == pep)
		bits.append("%s %s" % [PEP_WORDS[pep], str(SINCE.get(since + 1, "late"))])
	return "they've " + " and ".join(bits)


# ---------------------------------------------------------------------------
# Their record
# ---------------------------------------------------------------------------
## A plan in a sentence: its name, or "a balanced game".
static func phrase(plan: String) -> String:
	var k := MatchSim.plan_key(plan)
	return "a balanced game" if k == "balanced" else CoachReport.plan_label(k)


## Only the Defensive Press takes "the" (director, 2026-11-08); "the Attack
## Corridor" and "the Controlled Tempo" are wrong (director, 2026-11-09).
const THE := {"defensive": true}


## A plan as the report names it: "the Defensive Press", "Win Contest", "a
## balanced game".
static func called(plan: String) -> String:
	var k := MatchSim.plan_key(plan)
	return ("the " if THE.has(k) else "") + phrase(k)


## "in the third quarter" for quarter q (1-4), "in extra time" after.
static func in_quarter(q: int) -> String:
	if q >= 1 and q <= QUARTER_WORDS.size():
		return "in the %s quarter" % QUARTER_WORDS[q - 1]
	return "in extra time"


## A match's plans as a story, one plan key per quarter: "Melbourne started
## with A and switched to B in the third quarter." `subject` starts it;
## `span` is "game" or "half". "" for a balanced game throughout.
static func plan_story(subject: String, plans: Array, span := "game") -> String:
	var segs := []
	for i in range(plans.size()):
		var k := MatchSim.plan_key(str(plans[i]))
		if segs.is_empty() or str(segs[segs.size() - 1][0]) != k:
			segs.append([k, i + 1])
	if segs.is_empty():
		return ""
	if segs.size() == 1:
		if str(segs[0][0]) == "balanced":
			return ""
		return "%s played %s all %s." % [subject, called(str(segs[0][0])), span]
	var s := "%s started with %s" % [subject, called(str(segs[0][0]))]
	for j in range(1, segs.size()):
		var bit := "%s %s" % [called(str(segs[j][0])), in_quarter(int(segs[j][1]))]
		if segs.size() == 2:
			s += " and switched to " + bit
		elif j == 1:
			s += ", switched to " + bit
		elif j == segs.size() - 1:
			s += ", then " + bit
		else:
			s += ", " + bit
	return s + "."


## One side's calls in a played match, for the season record:
## {"l": round label, "v": the other club, "p": plan per quarter, "w": why
## per quarter (MatchSim.ai_why)}. {} when that side was not a rival
## coach's (no why recorded) or the match kept no plans.
static func record_row(res: Dictionary, side: int) -> Dictionary:
	var p := []
	var w := []
	for h in res.get("tactics_history", []):
		if not (h is Dictionary):
			return {}
		var why: Array = (h as Dictionary).get("why", [])
		var plans: Array = (h as Dictionary).get("plans", [])
		if why.size() < 2 or plans.size() < 2 or str(why[side]) == "":
			return {}
		p.append(MatchSim.plan_key(str((plans[side] as Dictionary).get("gameplan", "balanced"))))
		w.append(str(why[side]))
	if p.is_empty():
		return {}
	return {"l": str(res.get("label", "")), "v": str([res.get("home", ""), res.get("away", "")][1 - side]),
			"p": p, "w": w}


## What the scoreboard has had them play this season, from a club's record
## rows (record_row): "This season they've gone to Attack Corridor when
## chasing and Controlled Tempo when in front." A part is left out when it
## is their usual game (`usual`, the plan the report names first, which their
## coach keeps all season: GameState._settle_usual_plans), and so is the line
## when nothing is left or before SEASON_MIN matches.
static func season_line(rows: Array, usual: String) -> String:
	if rows.size() < SEASON_MIN:
		return ""
	var chase := {}
	var front := {}
	for r in rows:
		var p: Array = (r as Dictionary).get("p", [])
		var w: Array = (r as Dictionary).get("w", [])
		for i in range(mini(p.size(), w.size())):
			var plan := str(p[i])
			match str(w[i]):
				"chase", "lost_q":
					chase[plan] = int(chase.get(plan, 0)) + 1
				"protect":
					front[plan] = int(front.get(plan, 0)) + 1
	var bits := []
	var c := _top(chase)
	if c != "" and c != MatchSim.plan_key(usual):
		bits.append("%s when chasing" % called(c))
	var f := _top(front)
	if f != "" and f != MatchSim.plan_key(usual):
		bits.append("%s when in front" % called(f))
	if bits.is_empty():
		return ""
	return "This season they've gone to %s." % " and ".join(bits)


## Their last match against you this season, as a story: "Against you in
## Round 6, they started with ...". "" when they have not met you.
static func vs_line(rows: Array, me: String) -> String:
	for i in range(rows.size() - 1, -1, -1):
		var r: Dictionary = rows[i]
		if str(r.get("v", "")) != me:
			continue
		var story := plan_story("they", r.get("p", []))
		if story == "":
			story = "they played it straight all game."
		return "Against you %s, %s" % [where(str(r.get("l", ""))), story]
	return ""


## Their last match, as a story, when it was not against you (vs_line tells
## that one): "Last time out in Round 6, they started with ...". "" for a plain
## game or none played.
static func last_line(rows: Array, me: String) -> String:
	if rows.is_empty():
		return ""
	var r: Dictionary = rows[rows.size() - 1]
	if str(r.get("v", "")) == me:
		return ""
	var story := plan_story("they", r.get("p", []))
	return "" if story == "" else "Last time out %s, %s" % [where(str(r.get("l", ""))), story]


## "in Round 6", "in the Grand Final", "in the Qualifying Final" from a
## result's label.
static func where(label: String) -> String:
	var l := label.split(" · ")[0].strip_edges()
	if l == "":
		return "this season"
	if l.begins_with("Round"):
		return "in " + l
	var words := l.split(" ")
	if words.size() > 1 and words[words.size() - 1].is_valid_int():
		words.remove_at(words.size() - 1)
	return "in the " + " ".join(words)


# ---------------------------------------------------------------------------
static func _pace(plan: String) -> float:
	return float((MatchSim.PLANS.get(MatchSim.plan_key(plan), {}) as Dictionary).get("pace", 1.0))


static func _plan(c) -> String:
	return str((c as Dictionary).get("gameplan", "balanced")) if c is Dictionary else str(c)


static func _pep(c) -> String:
	return str((c as Dictionary).get("pep", "steady")) if c is Dictionary else "steady"


## What a quarter's call did to legs: plan pace times pep talk pace (the
## fatigue MatchSim._after_chain applies; Bring the heat burns legs only).
static func _cost(c) -> float:
	return _pace(_plan(c)) * float((PEPS.get(_pep(c), {}) as Dictionary).get("pace", 1.0))


## The first quarter (0-based) of the run of calls matching `pred` that ends
## with the last one; -1 when the last one does not match.
static func _run_start(calls: Array, pred: Callable) -> int:
	var start := calls.size()
	while start > 0 and pred.call(calls[start - 1]):
		start -= 1
	return start if start < calls.size() else -1


static func _top(counts: Dictionary) -> String:
	var best := ""
	var n := 0
	for k in ORDER:
		if int(counts.get(k, 0)) > n:
			n = int(counts[k])
			best = k
	return best


## "A", "A or B", "A, B or C".
static func _list(items: Array, word: String) -> String:
	if items.size() <= 1:
		return "" if items.is_empty() else str(items[0])
	var head := []
	for i in range(items.size() - 1):
		head.append(str(items[i]))
	return "%s %s %s" % [", ".join(head), word, str(items[items.size() - 1])]
