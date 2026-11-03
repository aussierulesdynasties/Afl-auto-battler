class_name MatchStory
extends RefCounted
## The match makes the story (director, 2026-11-03, plan step 1b): after every
## match, its hero, its turning point and why it was won or lost, in plain
## words. Pure: reads a MatchSim result, never writes it. Every number said is
## read from the result, and each reason carries the numbers it was built from
## ("mine", "theirs") so a test can trace it.
##
## Behind the switch "match_story" (Features), which ships off.

## A goal is clutch when it is kicked 20 minutes or more into the last quarter
## with the margin within two goals before it.
const CLUTCH_FROM := 20
const CLUTCH_MARGIN := 12
## Hero points on top of the match rating (MatchNotes.rating): a clutch goal,
## and a clearance (the engine's contested-ball stat: it keeps no separate
## contested-possession count).
const CLUTCH_POINTS := 10
const CLEARANCE_POINTS := 1
## Gaps worth a reason, smallest first in the order they are tried.
const EDGES := [
	["clearances", 4, "clearances"],
	["inside50", 6, "inside 50s"],
	["tackles", 8, "tackles"],
	["marks", 10, "marks"],
]
const MAX_REASONS := 3
## A close game: decided by two goals or less.
const CLOSE := 12


static func on() -> bool:
	return Features.on("match_story")


## {hero, turning_point, reasons, headline, won, margin, side}. {} for a result
## with no score. `side` is the point of view (0 home, 1 away).
static func build(res: Dictionary, side: int) -> Dictionary:
	var score: Array = res.get("score", [])
	if score.size() < 2:
		return {}
	var margin := int(score[side]) - int(score[1 - side])
	var hero := hero_of(res)
	return {
		"side": side, "margin": margin, "won": margin > 0, "drawn": margin == 0,
		"hero": hero, "turning_point": turning_point(res, side),
		"reasons": reasons(res, side), "headline": headline(res, side, hero),
	}


## The clutch goals in a result by player id: goals late in the last quarter
## (or extra time) with the game within two goals before the kick.
static func clutch_goals(res: Dictionary) -> Dictionary:
	var out := {}
	for ev in res.get("events", []):
		if str(ev.get("kind", "")) != "goal" or int(ev.get("q", 1)) < 4:
			continue
		if int(ev.get("q", 1)) == 4 and int(ev.get("min", 0)) - 90 < CLUTCH_FROM:
			continue
		var sc: Array = ev.get("score", [0, 0])
		var s := int(ev.get("side", 0))
		var before := (int(sc[s]) - 6) - int(sc[1 - s])
		if absi(before) <= CLUTCH_MARGIN:
			var id := str(ev.get("player_id", ""))
			if id != "":
				out[id] = int(out.get(id, 0)) + 1
	return out


## One player's hero points: the match rating, the clutch goals and the clearances.
static func hero_points(st: Dictionary, clutch: int) -> int:
	return MatchNotes.rating(st) + CLUTCH_POINTS * clutch \
			+ CLEARANCE_POINTS * int(float(st.get("clearances", 0.0)))


## The match hero: the winners' best by hero points (either side in a draw).
## {id, name, side, club, points, goals, disposals, tackles, clearances, clutch, line}.
static func hero_of(res: Dictionary) -> Dictionary:
	var score: Array = res.get("score", [0, 0])
	var sides := [0, 1]
	if int(score[0]) != int(score[1]):
		sides = [0 if int(score[0]) > int(score[1]) else 1]
	return best_of(res, sides)


## Your best player by the same hero points (director, 2026-11-03: a loss
## names both the winners' hero and your best). Same shape as hero_of.
static func my_best(res: Dictionary, side: int) -> Dictionary:
	return best_of(res, [side])


## The best by hero points over the given sides.
static func best_of(res: Dictionary, sides: Array) -> Dictionary:
	var clutch := clutch_goals(res)
	var codes := [str(res.get("home", "")), str(res.get("away", ""))]
	var best := {}
	for s in sides:
		for r in MatchNotes.rated_players(res, s):
			var st: Dictionary = r["stats"]
			var c := int(clutch.get(str(r["id"]), 0))
			var pts := hero_points(st, c)
			if best.is_empty() or pts > int(best["points"]):
				best = {"id": str(r["id"]), "name": str(r["name"]), "side": s, "club": codes[s],
						"points": pts, "clutch": c,
						"goals": int(float(st.get("goals", 0.0))),
						"disposals": int(float(st.get("disposals", 0.0))),
						"tackles": int(float(st.get("tackles", 0.0))),
						"clearances": int(float(st.get("clearances", 0.0))),
						"line": MatchNotes.game_line(st)}
	if not best.is_empty() and int(best["clutch"]) > 0:
		best["line"] = "%s, %s late with the game in the balance" % [str(best["line"]),
				"a goal" if int(best["clutch"]) == 1 else "%s goals" % MatchNotes.count_word(int(best["clutch"]))]
	return best


## The turning point, from the full-time logic (MatchNotes): the comeback, else
## the score that put the winners in front for good or a star lost hurt, else a
## run of four or more goals. "" for a match that never turned.
static func turning_point(res: Dictionary, side: int) -> String:
	var turn := ComebackTelling.turn_facts(res, side)
	if not turn.is_empty():
		return str(turn["text"])
	var tps := MatchNotes.turning_points(res, side)
	if not tps.is_empty():
		return str(tps[0])
	var run := MatchNotes._longest_run(res.get("events", []))
	if int(run["len"]) >= 4:
		var codes := [str(res.get("home", "")), str(res.get("away", ""))]
		var when := " in the %s quarter" % MatchNotes.QUARTER_NAMES[mini(int(run["q"]) - 1, 4)] if bool(run["one_q"]) else ""
		return "%s kicked %s unanswered goals%s." % [GameDB.club_name(codes[int(run["side"])]),
				MatchNotes.count_word(int(run["len"])), when]
	return ""


## Why we won or lost: one to three reasons, the biggest edge in the result's
## direction first, then what your calls did. Each is {text, stat, mine, theirs}:
## the two numbers it says, read from the result.
static func reasons(res: Dictionary, side: int) -> Array:
	var team: Array = res.get("team", [{}, {}])
	if team.size() < 2:
		return []
	var me: Dictionary = team[side]
	var op: Dictionary = team[1 - side]
	var score: Array = res.get("score", [0, 0])
	var margin := int(score[side]) - int(score[1 - side])
	var dir := 1 if margin >= 0 else -1
	var edges := []
	for e in EDGES:
		var a := int(float(me.get(e[0], 0.0)))
		var b := int(float(op.get(e[0], 0.0)))
		if (a - b) * dir >= int(e[1]):
			edges.append({"gap": float(absi(a - b)) / float(e[1]), "stat": str(e[0]), "mine": a, "theirs": b,
					"text": ("You won the %s %d to %d." if a > b else "They won the %s %d to %d.") % [e[2], a if a > b else b, b if a > b else a]})
	var pa := MatchSim.pressure_rating(me, op)
	var pb := MatchSim.pressure_rating(op, me)
	if (pa - pb) * dir >= MatchNotes.PRESSURE_GAP:
		edges.append({"gap": float(absi(pa - pb)) / float(MatchNotes.PRESSURE_GAP), "stat": "pressure_rating",
				"mine": pa, "theirs": pb,
				"text": ("Your pressure told: a rating of %d to %d." if pa > pb else "Their pressure told: a rating of %d to %d.") % [maxi(pa, pb), mini(pa, pb)]})
	edges.sort_custom(func(x, y): return float(x["gap"]) > float(y["gap"]))
	var out := []
	for e in edges.slice(0, 2):
		e.erase("gap")
		out.append(e)
	var call := call_reason(res, side, dir)
	if not call.is_empty():
		out.append(call)
	if out.is_empty():
		# Nothing stood out: the scoring shots and the kicking say it.
		var g: Array = res.get("goals", [0, 0])
		var bh: Array = res.get("behinds", [0, 0])
		var sa := int(g[side]) + int(bh[side])
		var sb := int(g[1 - side]) + int(bh[1 - side])
		out.append({"stat": "scoring_shots", "mine": sa, "theirs": sb,
				"text": "Scoring shots were %d to %d, and you kicked %d.%d to %d.%d." % [sa, sb,
				int(g[side]), int(bh[side]), int(g[1 - side]), int(bh[1 - side])]})
	return out.slice(0, MAX_REASONS)


## What your calls did, for the quarter that went most the result's way:
## the first "What your calls did" line for it (MatchNotes.calls_lines), with
## that quarter's score to each side. {} when no call was on record.
static func call_reason(res: Dictionary, side: int, dir: int) -> Dictionary:
	var qg: Array = res.get("q_goals", [])
	var qb: Array = res.get("q_behinds", [])
	var best_q := 0
	var best_m := 0
	for i in range(mini(qg.size(), 4)):
		var m := ((int(qg[i][side]) * 6 + int(qb[i][side])) - (int(qg[i][1 - side]) * 6 + int(qb[i][1 - side]))) * dir
		if m > best_m and not MatchNotes.calls_lines(res, side, i + 1).is_empty():
			best_m = m
			best_q = i + 1
	if best_q == 0:
		return {}
	var line := str(MatchNotes.calls_lines(res, side, best_q)[0])
	var i := best_q - 1
	var a := int(qg[i][side]) * 6 + int(qb[i][side])
	var b := int(qg[i][1 - side]) * 6 + int(qb[i][1 - side])
	return {"stat": "q%d_points" % best_q, "mine": a, "theirs": b, "quarter": best_q, "call": line,
			"text": "Your call in the %s quarter (%s to %d): %s" % [MatchNotes.QUARTER_NAMES[i],
			("won it %d" if a > b else "lost it %d") % a, b, line]}


## "Smith stars as Geelong beat Sydney by 23".
static func headline(res: Dictionary, side: int, hero: Dictionary) -> String:
	var score: Array = res.get("score", [0, 0])
	var codes := [str(res.get("home", "")), str(res.get("away", ""))]
	var diff := int(score[0]) - int(score[1])
	var tail: String
	if diff == 0:
		tail = "%s and %s draw" % [GameDB.club_name(codes[0]), GameDB.club_name(codes[1])]
	else:
		var w := 0 if diff > 0 else 1
		tail = "%s beat %s by %d" % [GameDB.club_name(codes[w]), GameDB.club_name(codes[1 - w]), absi(diff)]
	if hero.is_empty():
		return tail
	return "%s stars as %s" % [str(hero["name"]), tail]


## The record kept on GameState for later arcs: plain data only.
static func record(res: Dictionary, side: int, year: int) -> Dictionary:
	var st := build(res, side)
	if st.is_empty():
		return {}
	var codes := [str(res.get("home", "")), str(res.get("away", ""))]
	var hero: Dictionary = st["hero"]
	var reason_texts := []
	for r in st["reasons"]:
		reason_texts.append(str(r["text"]))
	var mine := {}
	if int(st["margin"]) < 0:
		mine = my_best(res, side)
	return {"year": year, "label": str(res.get("label", "")), "round": int(res.get("round", 0)),
			"club": codes[side], "opp": codes[1 - side], "margin": int(st["margin"]),
			"hero_id": str(hero.get("id", "")), "hero_name": str(hero.get("name", "")),
			"hero_club": str(hero.get("club", "")), "hero_line": str(hero.get("line", "")),
			"turning_point": str(st["turning_point"]), "reasons": reason_texts,
			"headline": str(st["headline"]),
			# Your best in a loss (empty in a win or draw).
			"my_best_id": str(mine.get("id", "")), "my_best_name": str(mine.get("name", "")),
			"my_best_line": str(mine.get("line", "")),
			# The match turned on a comeback (ComebackTelling): yours in a win, against you in a loss.
			"comeback": not ComebackTelling.turn_facts(res, side).is_empty(),
			"final": str(res.get("tag", "")) != ""}


## Your side's hero of a record: the hero when he is yours, else your best
## in a loss. {id, name} or {} (a draw's hero from the other side).
static func side_hero(rec: Dictionary) -> Dictionary:
	if str(rec.get("hero_club", "")) == str(rec.get("club", "")) and str(rec.get("hero_id", "")) != "":
		return {"id": str(rec["hero_id"]), "name": str(rec.get("hero_name", ""))}
	if str(rec.get("my_best_id", "")) != "":
		return {"id": str(rec["my_best_id"]), "name": str(rec.get("my_best_name", ""))}
	return {}


## Arc facts from the match stories of `year` (plan step 1b, for CoachArcs):
## hero_streak (your matches in a row, counted back from the last, with the
## same player of yours the hero), hero_counts {id: n} (your side's hero:
## my_best in a loss), last_hero_mine, last_hero_id, close_losses (by CLOSE
## or less), turned_against (losses that turned on a comeback against you).
static func arc_facts(stories: Array, year: int) -> Dictionary:
	var f := {"hero_streak": 0, "hero_counts": {}, "last_hero_mine": false, "last_hero_id": "",
			"close_losses": 0, "turned_against": 0}
	var ids := []
	for rec in stories:
		if int(rec.get("year", 0)) != year:
			continue
		var m := int(rec.get("margin", 0))
		if m < 0 and -m <= CLOSE:
			f["close_losses"] += 1
		if m < 0 and bool(rec.get("comeback", false)):
			f["turned_against"] += 1
		var sh := side_hero(rec)
		if not sh.is_empty():
			f["hero_counts"][sh["id"]] = int(f["hero_counts"].get(sh["id"], 0)) + 1
		ids.append(str(sh.get("id", "")))
	if not ids.is_empty():
		var last: String = ids[-1]
		f["last_hero_mine"] = last != ""
		f["last_hero_id"] = last
		if last != "":
			for i in range(ids.size() - 1, -1, -1):
				if ids[i] != last:
					break
				f["hero_streak"] += 1
	return f


## Fold one record into its season's digest (GameState.match_story_digest,
## keyed by the year as a string), so a season outlives the trimmed list:
## {played, heroes {id: {name, count}}, best_win, worst_loss, best_final_win,
## close_final_loss ({opp, margin, label, headline, turning_point} or {}),
## comebacks, comebacks_against, close_wins, close_losses}.
static func fold(digest: Dictionary, rec: Dictionary) -> void:
	var key := str(int(rec.get("year", 0)))
	if not digest.has(key):
		digest[key] = {"heroes": {}, "played": 0, "best_win": {}, "worst_loss": {}, "best_final_win": {},
				"close_final_loss": {}, "comebacks": 0, "comebacks_against": 0, "close_wins": 0, "close_losses": 0}
	var d: Dictionary = digest[key]
	d["played"] = int(d["played"]) + 1
	var sh := side_hero(rec)
	if not sh.is_empty():
		var h: Dictionary = (d["heroes"] as Dictionary).get(sh["id"], {"name": sh["name"], "count": 0})
		h["count"] = int(h["count"]) + 1
		d["heroes"][sh["id"]] = h
	var m := int(rec.get("margin", 0))
	var game := {"opp": str(rec.get("opp", "")), "margin": m, "label": str(rec.get("label", "")),
			"headline": str(rec.get("headline", "")), "turning_point": str(rec.get("turning_point", ""))}
	var fin := bool(rec.get("final", false))
	if m > 0:
		if (d["best_win"] as Dictionary).is_empty() or m > int(d["best_win"]["margin"]):
			d["best_win"] = game
		if fin and ((d["best_final_win"] as Dictionary).is_empty() or m > int(d["best_final_win"]["margin"])):
			d["best_final_win"] = game
		if m <= CLOSE:
			d["close_wins"] = int(d["close_wins"]) + 1
		if bool(rec.get("comeback", false)):
			d["comebacks"] = int(d["comebacks"]) + 1
	elif m < 0:
		if (d["worst_loss"] as Dictionary).is_empty() or m < int(d["worst_loss"]["margin"]):
			d["worst_loss"] = game
		if fin and ((d["close_final_loss"] as Dictionary).is_empty() or m > int(d["close_final_loss"]["margin"])):
			d["close_final_loss"] = game
		if -m <= CLOSE:
			d["close_losses"] = int(d["close_losses"]) + 1
		if bool(rec.get("comeback", false)):
			d["comebacks_against"] = int(d["comebacks_against"]) + 1


## The season's hero leader in a digest: {id, name, count} or {}. A tie goes
## to `tiebreak` {id: n} (the BF votes), then to the first to reach it.
static func season_hero(d: Dictionary, tiebreak := {}) -> Dictionary:
	var best := {}
	var heroes: Dictionary = d.get("heroes", {})
	for id in heroes:
		var n := int(heroes[id]["count"])
		if best.is_empty() or n > int(best["count"]) or (n == int(best["count"]) \
				and int(tiebreak.get(str(id), 0)) > int(tiebreak.get(str(best["id"]), 0))):
			best = {"id": str(id), "name": str(heroes[id]["name"]), "count": n}
	return best
