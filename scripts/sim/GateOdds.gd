class_name GateOdds
extends RefCounted
## What each match-day call does for you and what it costs, with the size as a
## percentage, in football words (bible §4, director 2026-10-18: "full
## transparency behind each decision and the impact it will have"; "both
## options carrying positives and negatives"). Every figure is worked out from
## the constant the sim itself uses; no template here holds a number of its
## own (tests/run_matchup_tests.gd, _gate_odds). Nothing here says which
## option is better.

const GAIN := "Gain: %s"
const COST := "Cost: %s"

# The game plans (M1, director 2026-11-10: "Gain for this list today", the
# written figure beside it). Templates hold no number of their own.
const PLAN_GAIN := {
	"attacking": "your shots %s more accurate, %s more ground a kick",
	"defensive": "%s more pressure where they start, their shots %s less accurate",
	"contest": "a %s better chance at every stoppage",
	"controlled": "%s fewer clangers, %s less pressure felt, legs tire %s slower",
}
const PLAN_COST := {
	"attacking": "%s more clangers, legs tire %s faster, their shots %s more accurate on the rebound",
	"defensive": "your shots %s less accurate, legs tire %s faster, %s less pressure in your back third, %s less ground a kick",
	"contest": "%s less ground a kick, their shots %s more accurate on the rebound",
	"controlled": "%s less ground a kick",
}
const PLAN_SUITS := " (%s for a list that suits it)"
const BALANCED_GAIN := "nothing for them to exploit: no plan cost"
const BALANCED_COST := "no plan edge at either end"

# The pep talk (M3), for the quarter it is given.
const PEP_GAIN := {
	"steady": "no extra wear on the legs and no frayed tempers",
	"fire_up": "a %s better chance at every contest while you are behind; nothing level or in front",
	"calm": "%s fewer clangers, %s less pressure felt, legs tire %s slower",
	"heat": "%s more pressure on their ball carriers (%s on top of a High Press)",
}
const PEP_COST := {
	"steady": "no lift at the contest and no extra pressure",
	"fire_up": "%s more clangers and legs tire %s faster, behind or not",
	"calm": "%s less ground a kick",
	"heat": "legs tire %s faster all quarter",
}

# Who tags (the pre-bounce and break sheets).
const TAG_GIVES := "%s of his own ball and contest work"
# What the tag does to their man, in his touches a match (director, 2026-11-10).
const TAG_TOUCHES := "Usually %d touches. Tagged, about %d."
# The Tag call at a break (director 2026-11-10, "Gain / Cost everywhere"):
# labelled rows like every other break call, the size inside the line.
const TAG_BREAK_GAIN := "%s usually gets %d touches; with %s on him, about %d"
const TAG_BENCH_COST := "%s goes while %s is on the bench, and gives up %s"
const TAG_NOBODY_GAIN := "none: you have no midfielder on the ground to go to him"
const TAG_NONE_GAIN := "your midfielders play their own game: nobody gives up %s"
const TAG_NONE_COST_ANY := "their midfielders get their usual touches"
# The call when their midfielder is kicking a bag.
const TAG_HOT_GAIN := "%s usually gets %d touches; with %s on him, about %d, until you call it off"
const TAG_HOT_COST := "%s gives up %s"
const TAG_LEAVE_GAIN := "your midfielders play their own game"
const TAG_LEAVE_COST := "%s gets his usual %d touches"
## The same call with a tag already on another of theirs: the man who goes is
## already giving up his own game, so moving him costs the hold he has now.
const TAG_MOVE_COST := "the tag comes off %s, who goes back to his usual %d touches"
const TAG_STAY_GAIN := "%s stays on %s, who is held to about %d touches"

# Skip to full time.
const SKIP_FIRST := "Skip plays the match on the plan you took in, no tag, no talk. Nothing changed here is kept; every call in the match takes 'no change'."
const SKIP_LATER := "Skip plays the rest on last quarter's calls and talk. Nothing changed here is kept; every call in the match takes 'no change'."

# The in-match risk cards.
const BURST_GAIN := {
	"surge": "a %s better chance at every contest, your shots %s more accurate",
	"hold": "%s fewer clangers, %s less pressure felt, their shots %s less accurate",
	"stack": "a %s better chance at each centre bounce (never above %s)",
	"flood": "their shots %s less accurate",
	"push": "your shots %s more accurate, %s more ground a kick",
}
const BURST_COST := {
	"surge": "their shots %s more accurate, legs tire %s faster",
	"hold": "your shots %s less accurate, %s less ground a kick",
	"stack": "their shots %s more accurate meanwhile",
	"flood": "your shots %s less accurate, %s less ground a kick",
	"push": "their shots %s more accurate",
}
const FOR_MINUTES := ", for about %d minutes"
const TO_SIREN := ", to the final siren"
const TO_BREAK := ", to the break"
const NONE_GAIN := "no extra risk at either end"
const NONE_COST_RUN := "their run goes on at the current odds"
const NONE_COST_BOUNCE := "no extra numbers behind the ball or ahead of it"


static func pct(share: float) -> String:
	return Conditioning.pct(absf(share))


## "about N%": a whole figure, for odds that are an estimate of reach.
static func about_pct(share: float) -> String:
	return "%d%%" % roundi(absf(share) * 100.0)


static func gain(s: String) -> String:
	return GAIN % s


static func cost(s: String) -> String:
	return COST % s


## The share of his own game a tagger gives up: his contest worth
## (TAGGER_COST) and his ball (1 - TAGGER_BALL), one figure when they agree.
static func tag_gives_pct() -> String:
	var contest := pct(MatchSim.TAGGER_COST)
	var ball := pct(1.0 - MatchSim.TAGGER_BALL)
	return contest if contest == ball else "%s of his ball and %s" % [ball, contest]


static func tag_gives() -> String:
	return TAG_GIVES % tag_gives_pct()


## Their man's touches a match untagged, and with `tagger` on him at `legs`:
## the sim's multiplier (MatchSim._tag_share) as measured in matches, on `target`'s
## own usual touches (Roles.usual_touches; row 178). No `target`: the measured man.
static func usual_touches(target: Dictionary = {}) -> int:
	return roundi(Roles.usual_touches(target))


static func tag_kept(tagger: Dictionary, legs: float, target: Dictionary = {}) -> int:
	return roundi(Roles.tag_touches(tagger, legs, target))


static func tag_touches(tagger: Dictionary, legs: float, target: Dictionary = {}) -> String:
	return TAG_TOUCHES % [usual_touches(target), tag_kept(tagger, legs, target)]


## The four lines of the in-match tag call (MatchSim "hot"): their midfielder
## `hot_name` (usually `usual` touches) has kicked a bag, `stopper` would go to him
## and hold him to `kept`. `on_now` is the man `stopper` is already tagging, "" for
## none: then moving the tag costs that hold (`now_kept` of his `now_usual`), and
## leaving it keeps it.
static func tag_call_lines(hot_name: String, stopper: String, kept: int, usual: int,
		on_now: String = "", now_usual: int = 0, now_kept: int = 0) -> Dictionary:
	var moving := on_now != ""
	return {
		"tag_gain": gain(TAG_HOT_GAIN % [hot_name, usual, stopper, kept]),
		"tag_cost": cost(TAG_MOVE_COST % [on_now, now_usual] if moving else TAG_HOT_COST % [stopper, tag_gives()]),
		"leave_gain": gain(TAG_STAY_GAIN % [stopper, on_now, now_kept] if moving else TAG_LEAVE_GAIN),
		"leave_cost": cost(TAG_LEAVE_COST % [hot_name, usual]),
	}


## The break Tag call's Gain / Cost, unlabelled: [gain, cost]. `target` is the
## man tagged ("" for no tag) and `usual` his touches untagged; `who` the
## midfielder who goes ("" when you have none on the ground) and `kept` the
## touches he holds him to; `benched` your named tagger when he is on the bench
## and `who` goes in his place. With no tag, `their_best` is the midfielder of
## theirs who goes untagged ("" for any) and `best_usual` his touches.
static func tag_break_texts(target: String, who: String, kept: int, usual: int, benched := "",
		their_best := "", best_usual := 0) -> Array:
	if target == "":
		return [TAG_NONE_GAIN % tag_gives(),
				TAG_LEAVE_COST % [their_best, best_usual] if their_best != "" else TAG_NONE_COST_ANY]
	if who == "":
		return [TAG_NOBODY_GAIN, TAG_LEAVE_COST % [target, usual]]
	var gave := TAG_BENCH_COST % [who, benched, tag_gives()] if benched != "" else TAG_HOT_COST % [who, tag_gives()]
	return [TAG_BREAK_GAIN % [target, usual, who, kept], gave]


static func skip_line(q: int) -> String:
	return SKIP_FIRST if q <= 1 else SKIP_LATER


## How long a burst lasts: every call ends at the break, so one that outlasts
## the quarter runs to the break (the siren in the last quarter).
static func burst_time(kind: String, minutes_left: int, last := true) -> String:
	var chains := int((MatchSim.BURSTS.get(kind, {}) as Dictionary).get("chains", 0))
	var mins := roundi(float(chains) * float(MatchSim.GAME_MINUTES) / float(Ratings.T["chains_per_game"]))
	if minutes_left >= 0 and mins >= minutes_left:
		return TO_SIREN if last else TO_BREAK
	return FOR_MINUTES % mins


static func burst_lines(kind: String, minutes_left := -1, last := true) -> Array:
	var t := burst_time(kind, minutes_left, last)
	match kind:
		"surge":
			return [BURST_GAIN[kind] % [pct(MatchSim.SURGE_CONTEST), pct(MatchSim.SURGE_GOAL - 1.0)] + t,
					BURST_COST[kind] % [pct(MatchSim.SURGE_OPP_GOAL - 1.0), pct(MatchSim.SURGE_PACE - 1.0)]]
		"hold":
			return [BURST_GAIN[kind] % [pct(1.0 - MatchSim.HOLD_CLANGERS), pct(1.0 - MatchSim.HOLD_TAKEN),
					pct(1.0 - MatchSim.HOLD_OPP_GOAL)] + t,
					BURST_COST[kind] % [pct(1.0 - MatchSim.HOLD_GOAL), pct(1.0 - MatchSim.BACK_GAIN)]]
		"stack":
			return [BURST_GAIN[kind] % [pct(MatchSim.STACK_CONTEST), pct(float(Ratings.T["contest_clamp"]))] + t,
					BURST_COST[kind] % pct(MatchSim.STACK_OPP_GOAL - 1.0)]
		"flood":
			return [BURST_GAIN[kind] % pct(1.0 - MatchSim.FLOOD_OPP_GOAL) + t,
					BURST_COST[kind] % [pct(1.0 - MatchSim.FLOOD_GOAL), pct(1.0 - MatchSim.BACK_GAIN)]]
		"push":
			return [BURST_GAIN[kind] % [pct(MatchSim.PUSH_GOAL - 1.0), pct(MatchSim.PUSH_GAIN - 1.0)] + t,
					BURST_COST[kind] % pct(MatchSim.PUSH_OPP_GOAL - 1.0)]
	return ["", ""]


static func _plan_v(plan: String, key: String, fallback := 1.0) -> float:
	return float((MatchSim.PLANS.get(plan, {}) as Dictionary).get(key, fallback))


## A plan's gain and cost as figures: [gain shares, cost shares], each share
## the written one times `up` (gain) or `down` (cost), as MatchSim._pv does.
static func plan_shares(plan: String, up := 1.0, down := 1.0) -> Array:
	var v := func(k: String) -> float: return absf(_plan_v(plan, k) - 1.0)
	match plan:
		"attacking":
			return [[v.call("goal") * up, v.call("gain") * up],
					[v.call("clangers") * down, v.call("pace") * down, v.call("exposed") * down]]
		"defensive":
			var zone: Array = MatchSim.PRESS_PLAN_ZONE
			return [[(float(zone[0]) - 1.0) * up, v.call("opp_goal") * up],
					[v.call("goal") * down, v.call("pace") * down, (1.0 - float(zone[2])), v.call("gain") * down]]
		"contest":
			return [[_plan_v(plan, "contest", 0.0) * up], [v.call("gain") * down, v.call("exposed") * down]]
		"controlled":
			return [[v.call("clangers") * up, v.call("taken") * up, v.call("pace") * up], [v.call("gain") * down]]
	return [[], []]


static func _pcts(shares: Array) -> Array:
	return shares.map(func(x): return pct(float(x)))


## "5% and 6%", "8%, 4% and 5%".
static func _and(items: Array) -> String:
	if items.size() <= 1:
		return "".join(items)
	return ", ".join(items.slice(0, items.size() - 1)) + " and " + str(items[-1])


## A plan's gain and cost for this list today, unlabelled: [gain, cost].
## `up` and `down` come from MatchSim.upside_scale and cost_scale; the
## written figures follow the gain when today's differ.
## `best_up` is the gain scale a list that suits the plan as well as a list
## can (PlanFit.FIT_MAX) would get with everything else the same; -1 means the
## written plan on such a list. Today's gain never tops it.
static func plan_texts(plan: String, up := 1.0, down := 1.0, best_up := -1.0) -> Array:
	plan = MatchSim.plan_key(plan)
	if not PLAN_GAIN.has(plan):
		return [BALANCED_GAIN, BALANCED_COST]
	if best_up < 0.0:
		best_up = PlanFit.FIT_MAX
	var today := plan_shares(plan, up, down)
	var suits := plan_shares(plan, best_up)
	var g := str(PLAN_GAIN[plan]) % _pcts(today[0])
	if _pcts(today[0]) != _pcts(suits[0]):
		g += PLAN_SUITS % _and(_pcts(suits[0]))
	return [g, str(PLAN_COST[plan]) % _pcts(today[1])]


## The same as "Gain: ..." and "Cost: ..." lines.
static func plan_lines(plan: String, up := 1.0, down := 1.0) -> Array:
	var t := plan_texts(plan, up, down)
	return [gain(str(t[0])), cost(str(t[1]))]


## A plan's texts for a squad as it would take the field (CoachEffects applied).
static func plan_texts_for(sq: Squad, plan: String, weather_key := "perfect") -> Array:
	var up := MatchSim.upside_scale(sq, plan, weather_key)
	# Your own plan (CustomPlan): its strength sized for this list today, its
	# cost as written. Not built yet: no edge and no cost.
	if MatchSim.plan_key(plan) == CustomPlan.KEY:
		var own := CustomPlan.texts(sq.custom_plan, up)
		return own if not own.is_empty() else [BALANCED_GAIN, BALANCED_COST]
	var fit := PlanFit.fit(sq.ground, MatchSim.plan_key(plan))
	var best := up / fit * PlanFit.FIT_MAX if fit > 0.0 else -1.0
	return plan_texts(plan, up, MatchSim.cost_scale(sq, plan), best)


## A pep talk's gain and cost for the quarter, unlabelled: [gain, cost], from
## the multipliers MatchSim._pep_mult, _contest_pep and _pep_heat use.
## `contest` is Fire them up's lift at the contest (MatchSim.fire_up_contest,
## which carries an own plan's Fire them up lever); the base lift when no sim is at hand.
static func pep_texts(key: String, contest := MatchSim.PEP_FIRE_CONTEST) -> Array:
	var c: Dictionary = MatchSim.PEP_CALM
	var f: Dictionary = MatchSim.PEP_FIRE
	var d := func(m: Dictionary, k: String) -> String: return pct(float(m.get(k, 1.0)) - 1.0)
	match key:
		"fire_up":
			return [PEP_GAIN[key] % pct(contest), PEP_COST[key] % [d.call(f, "clangers"), d.call(f, "pace")]]
		"calm":
			return [PEP_GAIN[key] % [d.call(c, "clangers"), d.call(c, "taken"), d.call(c, "pace")], PEP_COST[key] % d.call(c, "gain")]
		"heat":
			var press := MatchSim.PEP_HEAT_PRESS - 1.0
			return [PEP_GAIN[key] % [pct(press), pct(press * MatchSim.PEP_HEAT_ON_PRESS)],
					PEP_COST[key] % d.call(MatchSim.PEP_HEAT, "pace")]
	return [PEP_GAIN["steady"], PEP_COST["steady"]]


# Play through (M5): the ball shared out differently, not more of it.
const FOCUS_GAIN := {
	"focus_mid": "%s gets the ball %s more often through the midfield, and keeps getting it to about %d touches before it spreads again (%d for anyone else)",
	"focus_fwd": "%s gets the ball %s more often up forward and takes %s more of the shots",
	"focus_def": "%s gets %s more of the first use out of the back half",
}
const FOCUS_COST := {
	"focus_mid": "the side's ball doesn't grow: the rest of the midfield gets less of it, and he runs %s further",
	"focus_fwd": "the shots don't grow: a better-placed forward shoots less often, and he runs %s further",
	"focus_def": "the ball out doesn't grow: the other backs get less first use, and he runs %s further",
}
const FOCUS_NONE_GAIN := "the ball finds whoever is best placed"
const FOCUS_NONE_COST := "nobody gets the extra ball"


## A play-through call's gain and cost, unlabelled: [gain, cost]. `who` is
## his name, "" for nobody.
static func focus_texts(slot: String, who: String) -> Array:
	if who == "":
		return [FOCUS_NONE_GAIN, FOCUS_NONE_COST]
	var run := pct(MatchSim.GPS_FOCUS_MULT - 1.0)
	match slot:
		"focus_fwd":
			return [FOCUS_GAIN[slot] % [who, pct(MatchSim.FOCUS_CARRY - 1.0), pct(MatchSim.FOCUS_SHOT - 1.0)], FOCUS_COST[slot] % run]
		"focus_def":
			return [FOCUS_GAIN[slot] % [who, pct(MatchSim.FOCUS_EXIT - 1.0)], FOCUS_COST[slot] % run]
	return [FOCUS_GAIN["focus_mid"] % [who, pct(MatchSim.FOCUS_CARRY - 1.0), roundi(MatchSim.USAGE_START_FOCUSED),
			roundi(MatchSim.USAGE_START)], FOCUS_COST["focus_mid"] % run]


# Defensive set-up (M6), sized for the men in the jobs.
const LOOSE_GAIN := "%s gets to about %s of their entries and makes the mark harder when he does"
const LOOSE_COST := "he leaves his man on about %s of entries; when he is late or loses, their shot is up to %s more dangerous"
const COVER_GAIN := "%s reaches %s fewer contests with %s on him"
const COVER_COST := "%s is %s less often a target inside 50"
const MAN_GAIN := "every defender holds his man: no space opens behind a loose man"
const MAN_COST := "nobody spare to cut off their entries%s"
const MAN_COST_SPARE := ", and %s plays free"


## How often a loose defender gets to an entry's contest, as the sim reaches
## it (MatchSim._loose_reach, before a forward drags him).
static func loose_reach(p: Dictionary) -> float:
	var read := clampf((Matchups.interceptor_score(p) - MatchSim.LOOSE_READ_FLOOR) / MatchSim.LOOSE_READ_SPAN, 0.0, 1.0)
	var r := MatchSim.LOOSE_REACH_MIN + MatchSim.LOOSE_REACH_RANGE * read
	return r * (MatchSim.ROAM_REACH if MatchSim.zone_intercepts else 1.0)


## A defensive set-up's gain and cost, unlabelled: [gain, cost]. `loose` and
## `minder` are the men in the jobs ({} when not in the set-up); `spare` is
## their loose man ({} when they have none).
static func defence_texts(key: String, loose: Dictionary, minder: Dictionary, spare: Dictionary) -> Array:
	var gains := PackedStringArray()
	var costs := PackedStringArray()
	if (key == "loose" or key == "both") and not loose.is_empty():
		gains.append(LOOSE_GAIN % [GameDB.player_display_name(loose), about_pct(loose_reach(loose))])
		var go := MatchSim.LOOSE_GO * (MatchSim.ROAM_REACH if MatchSim.zone_intercepts else 1.0)
		costs.append(LOOSE_COST % [about_pct(go), pct(float(MatchSim.LOOSE_LATE_SPACE["marked"]))])
	if (key == "cover" or key == "both") and not minder.is_empty() and not spare.is_empty():
		var roam := float(MatchSim.MINDER_ROAM["specialist" if Traits.has(minder, "def_forward") else "other"])
		gains.append(COVER_GAIN % [GameDB.player_display_name(spare), pct(1.0 - roam), GameDB.player_display_name(minder)])
		costs.append(COVER_COST % [GameDB.player_display_name(minder), pct(1.0 - MatchSim.MINDER_INVOLVE)])
	if gains.is_empty():
		var free := MAN_COST_SPARE % GameDB.player_display_name(spare) if not spare.is_empty() else ""
		return [MAN_GAIN, MAN_COST % free]
	return ["; ".join(gains), "; ".join(costs)]


# The set shot (M7): the odds the card plays. One short line each, so three
# choices and their six lines leave both men in the picture on a 360 px phone.
const SHOT_GAIN := "%s goal, %s behind"
const SHOT_COST := "%s it scores nothing"
const PASS_GAIN := "%s it reaches him, then %s goal"
const PASS_COST := "%s it is cut off, no shot"
const BOMB_GAIN := "%s goal out of the pack, %s behind"
const BOMB_COST := "%s the defence clears it"


## A set-shot option's gain and cost, labelled: [gain, cost]. Whole figures:
## the odds of one kick, not a measured rate.
static func set_shot_lines(o: Dictionary) -> Array:
	var g := float(o.get("goal", 0.0))
	match str(o.get("key", "")):
		"pass":
			var pp := float(o.get("pass", 0.0))
			return [gain(PASS_GAIN % [about_pct(pp), about_pct(float(o.get("mate_goal", 0.0)))]),
					cost(PASS_COST % about_pct(1.0 - pp))]
		"bomb":
			# The pack's real dice (MatchSim.bomb_odds), not the figures the
			# coach's default weighs.
			var bg := float(o.get("show_goal", g))
			var b := float(o.get("show_behind", o.get("behind", 0.0)))
			return [gain(BOMB_GAIN % [about_pct(bg), about_pct(b)]), cost(BOMB_COST % _rest_pct(bg, b))]
	var bh := float(o.get("behind", 0.0))
	return [gain(SHOT_GAIN % [about_pct(g), about_pct(bh)]), cost(SHOT_COST % _rest_pct(g, bh))]


## What is left of 100% once the goal and behind figures are rounded, so the
## three a card shows always add up.
static func _rest_pct(goal: float, behind: float) -> String:
	return "%d%%" % maxi(0, 100 - roundi(goal * 100.0) - roundi(behind * 100.0))
