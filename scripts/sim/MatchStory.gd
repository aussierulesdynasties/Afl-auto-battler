class_name MatchStory
extends RefCounted
## The match makes the story (director, 2026-11-03, plan step 1b): after every
## match, its hero, its turning point and why it was won or lost, in plain
## words. Pure: reads a MatchSim result, never writes it. Every number said is
## read from the result, and each reason carries the numbers it was built from
## ("mine", "theirs") so a test can trace it.

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


## {hero, turning_point, turning_fact, reasons, headline, won, margin, side}.
## {} for a result with no score. `side` is the point of view (0 home, 1 away).
## `turning_fact` names the fact the turning point states (MatchNotes'
## match_factor_items keys), "" when none.
static func build(res: Dictionary, side: int) -> Dictionary:
	var score: Array = res.get("score", [])
	if score.size() < 2:
		return {}
	var margin := int(score[side]) - int(score[1 - side])
	var hero := hero_of(res)
	var tp := turning_item(res, side)
	return {
		"side": side, "margin": margin, "won": margin > 0, "drawn": margin == 0,
		"hero": hero, "turning_point": str(tp.get("text", "")), "turning_fact": str(tp.get("fact", "")),
		"turning_also": tp.get("also", []),
		"reasons": reasons(res, side), "headline": headline(res, side, hero),
	}


## What a built story has told, for the sections under it to leave out
## (director's bug report, 2026-11-06: the same fact twice on full time): the
## turning point's fact, each reason's fact (a quarter's call also as
## "call:<line>"), and "=" + each sentence normalised (MatchNotes.norm_sentence).
static func told_facts(st: Dictionary) -> Dictionary:
	var out := {}
	if st.is_empty():
		return out
	var tp := str(st.get("turning_point", ""))
	if tp != "":
		out["=" + MatchNotes.norm_sentence(tp)] = true
		var tf := str(st.get("turning_fact", ""))
		if tf != "":
			out[tf] = true
		# The comeback and the goal that put a side in front for good are one
		# moment told two ways: the turning point says it, How it went does not.
		if tf == "turn" or tf == "turn:lead":
			out["turn"] = true
			out["turn:lead"] = true
		# The goal run the comeback was made of is the same moment again.
		for f in st.get("turning_also", []):
			out[str(f)] = true
	for r in st.get("reasons", []):
		out["=" + MatchNotes.norm_sentence(str(r.get("text", "")))] = true
		var stat := str(r.get("stat", ""))
		if stat == "scoring_shots":
			out["kicking"] = true
		elif r.has("quarter"):
			out["q%d" % int(r["quarter"])] = true
			out["call:" + str(r.get("call", ""))] = true
		elif stat != "":
			out[stat] = true
	return out


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
						"line": MatchNotes.game_line(st), "stat_line": MatchNotes.game_line(st)}
	if best.is_empty():
		return best
	best["late"] = ""
	if int(best["clutch"]) > 0:
		best["late"] = "%s late with the game in the balance" % [
				"a goal" if int(best["clutch"]) == 1 else "%s goals" % MatchNotes.count_word(int(best["clutch"]))]
		best["line"] = "%s, %s" % [str(best["line"]), str(best["late"])]
	return best


## A best player's line less the numbers another line on screen already
## gives him (`shown`, e.g. his Best players line "4 goals, 22 disposals"):
## full time says each fact once (director's bug report, 2026-11-06). The late
## goals clause always stays. "" when nothing is left.
static func line_less(best: Dictionary, shown: String) -> String:
	var have := {}
	for b in shown.split(", ", false):
		have[b.strip_edges()] = true
	var bits := PackedStringArray()
	for b in str(best.get("stat_line", best.get("line", ""))).split(", ", false):
		if not have.has(b.strip_edges()):
			bits.append(b.strip_edges())
	if str(best.get("late", "")) != "":
		bits.append(str(best["late"]))
	var out := ", ".join(bits)
	return out.left(1).to_upper() + out.substr(1) if out != "" else ""


## The turning point, from the full-time logic (MatchNotes): the comeback, else
## the score that put the winners in front for good or a star lost hurt, else a
## run of four or more goals. "" for a match that never turned.
static func turning_point(res: Dictionary, side: int) -> String:
	return str(turning_item(res, side).get("text", ""))


## The turning point with the fact it states: {fact, text, also}, {} for none.
## `also` lists other facts it covers: a comeback in the quarters of the
## match's goal run, or the winners going in front for good in the quarter
## their run began, is that run told another way ("run").
static func turning_item(res: Dictionary, side: int) -> Dictionary:
	var run := MatchNotes._longest_run(res.get("events", []))
	var long_run := int(run["len"]) >= 4
	var turn := ComebackTelling.turn_facts(res, side)
	if not turn.is_empty():
		var also := []
		var t := ComebackTelling.turning_quarter(res, side)
		if long_run and int(run["side"]) == int(t.get("side", -1)) 				and (turn.get("quarters", []) as Array).has(int(run["q"])):
			also.append("run")
		return {"fact": "turn", "text": str(turn["text"]), "also": also}
	var tps := MatchNotes.turning_point_items(res, side)
	if not tps.is_empty():
		var tp: Dictionary = tps[0]
		var also2 := []
		if str(tp["fact"]) == "turn:lead" and long_run and int(run["side"]) == int(tp["side"]) 				and int(run["q"]) == int(tp["q"]):
			also2.append("run")
		return {"fact": str(tp["fact"]), "text": str(tp["text"]), "also": also2}
	if long_run:
		return {"fact": "run", "text": MatchNotes.run_sentence(res, run)}
	return {}


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


## What the "What your calls did" line's slot is in the impact ledger.
## Players to go through have no ledger cause of their own.
const CALL_SLOT_CAUSE := {"gameplan": "gameplan", "tag_id": "tag"}


## What your calls did, for the quarter that went most the result's way:
## a "What your calls did" line for it (MatchNotes.calls_lines), with that
## quarter's score to each side. Only a call whose ledger figure, as its own
## row on "Our calls" shows it, went the result's way is cited, so a win is never put
## down to a call the same screen says cost us (director, 2026-11-12); failing
## that, the next quarter's call, else {}.
static func call_reason(res: Dictionary, side: int, dir: int) -> Dictionary:
	var qg: Array = res.get("q_goals", [])
	var qb: Array = res.get("q_behinds", [])
	# The points each call shows on Our calls; a call folded into "Our other
	# calls" has no figure of its own there, so it is not cited either.
	var shown := {}
	for r in calls(res, side).get("rows", []):
		if str(r["kind"]) == "call":
			shown[str(r["cause"])] = int(r["pts"])
	var qs := []
	for i in range(mini(qg.size(), 4)):
		var m := ((int(qg[i][side]) * 6 + int(qb[i][side])) - (int(qg[i][1 - side]) * 6 + int(qb[i][1 - side]))) * dir
		if m > 0:
			qs.append([m, i])
	qs.sort_custom(func(x, y): return int(x[0]) > int(y[0]) or (int(x[0]) == int(y[0]) and int(x[1]) < int(y[1])))
	for pair in qs:
		var i := int(pair[1])
		for e in MatchNotes._calls_entries(res, side, i + 1):
			var cause := str(CALL_SLOT_CAUSE.get(str(e["key"]), ""))
			if cause == "" or int(shown.get(cause, 0)) * dir <= 0:
				continue
			var line := str(e["line"])
			var a := int(qg[i][side]) * 6 + int(qb[i][side])
			var b := int(qg[i][1 - side]) * 6 + int(qb[i][1 - side])
			return {"stat": "q%d_points" % (i + 1), "mine": a, "theirs": b, "quarter": i + 1, "call": line,
					"cause": cause, "text": "Your call in the %s quarter (%s to %d): %s" % [MatchNotes.QUARTER_NAMES[i],
					("won it %d" if a > b else "lost it %d") % a, b, line]}
	return {}


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
	var rows := coach_rows(res, side)
	var all_names := call_names(res, side)
	var names := {}
	for cause in rows["mine"]:
		names[cause] = all_names[cause]
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
			"final": str(res.get("tag", "")) != "",
			# The impact ledger's coach rows (row 144, director 2026-11-10: "Yes, keep
			# them") and the name of each of our calls: calls_from() retells them.
			"coach_rows": rows, "call_names": names}


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


## Our calls at full time (row 144; design bible principle 3: the game shows
## what each decision led to). Read from the result's impact ledger
## (MatchSim.impact): the coach's rows are MatchSim.DECISION_CAUSES, the
## points each call added to its side's margin, worked out from where the
## ball went. Our biggest calls each get a row, the rest of ours one row,
## theirs one row, and the players and the bounce what is left, so the rows
## add up to the margin exactly.
const MAX_CALL_ROWS := 3


## The ledger's coach rows from `side`'s point of view: {"mine": {cause: pts},
## "theirs": {cause: pts}}, each side's own credit, calls not made left out.
## What the save keeps per match (MatchStory.record "coach_rows").
static func coach_rows(res: Dictionary, side: int) -> Dictionary:
	var imp: Array = res.get("impact", [])
	var out := {"mine": {}, "theirs": {}}
	if imp.size() < 2:
		return out
	for cause in MatchSim.DECISION_CAUSES:
		for k in [["mine", side], ["theirs", 1 - side]]:
			var pts := snappedf(float((imp[k[1]] as Dictionary).get(cause, 0.0)), 0.01)
			if pts != 0.0:
				out[k[0]][cause] = pts
	return out


## Who or what each of our calls was, for its row: {cause: "Our tag on Smith"}.
## The game plan and the pep talk from the plans we ran each quarter
## (tactics_history); the loose man, the defensive forward and the tag from
## who earned the ledger's credit (MatchSim.impact_by), so a man sent loose by
## the assistant or tagged from a moment card is the one named.
static func call_names(res: Dictionary, side: int) -> Dictionary:
	var plans := []
	var peps := []
	for h in res.get("tactics_history", []):
		var p: Dictionary = ((h as Dictionary).get("plans", [{}, {}]) as Array)[side]
		for pair in [[plans, MatchSim.plan_key(str(p.get("gameplan", "balanced")))], [peps, str(p.get("pep", "steady"))]]:
			if str(pair[1]) != "" and not (pair[0] as Array).has(pair[1]):
				(pair[0] as Array).append(pair[1])
	var by: Array = res.get("impact_by", [])
	var mine: Dictionary = by[side] if by.size() == 2 and by[side] is Dictionary else {}
	var out := {
		"gameplan": ("Our %s game plan" % CoachReport.plan_label(str(plans[0]))) if plans.size() == 1 else "Our game plans",
		"tag": "Our tag",
		"loose": "Our loose man",
		"minder": "Our defensive forward",
		"pep": "Our pep talks",
		"bursts": "Our calls in play",
		"moments": "Our calls at the moments",
	}
	var men := _earners(res, mine.get("tag", {}))
	if not men.is_empty():
		out["tag"] = ("Our tag on %s" if men.size() == 1 else "Our tags on %s") % _men_line(men)
	men = _earners(res, mine.get("loose", {}))
	if not men.is_empty():
		out["loose"] = ("%s as our loose man" if men.size() == 1 else "%s as our loose men") % _men_line(men)
	men = _earners(res, mine.get("minder", {}))
	if not men.is_empty():
		out["minder"] = ("%s as our defensive forward" if men.size() == 1
				else "%s as our defensive forwards") % _men_line(men)
	peps.erase("steady")
	if peps.size() == 1:
		out["pep"] = "Our pep talk, %s" % CoachReport.pep_label(str(peps[0]))
	return out


## The men who earned a named call's credit ({id: points}), biggest share
## first, by name; a man worth under half a point is left out unless he is
## the only one. [] with nobody on record.
static func _earners(res: Dictionary, credit) -> Array:
	if not credit is Dictionary or (credit as Dictionary).is_empty():
		return []
	var ids: Array = (credit as Dictionary).keys()
	ids.sort_custom(func(a, b): return absf(float(credit[a])) > absf(float(credit[b])))
	# Name only men whose points went the same way as the row's total, so a
	# man who cost us is never named on a row that shows a gain.
	var total := 0.0
	for id in ids:
		total += float(credit[id])
	var same := ids.filter(func(id): return float(credit[id]) * total >= 0.0)
	if same.is_empty():
		same = ids
	var out := []
	for id in same:
		if out.is_empty() or absf(float(credit[id])) >= 0.5:
			out.append(_name_in(res, str(id)))
	return out


## "Smith", "Smith and Jones", or "Smith and others".
static func _men_line(names: Array) -> String:
	if names.size() == 1:
		return str(names[0])
	if names.size() == 2:
		return "%s and %s" % [names[0], names[1]]
	return "%s and others" % names[0]


## A player's name from the result's team sheet, else the database.
static func _name_in(res: Dictionary, id: String) -> String:
	for side_list in res.get("roster", []):
		for r in side_list:
			if r is Dictionary and str(r.get("id", "")) == id:
				return str(r.get("name", ""))
	return GameDB.player_display_name_by_id(id, "him")


## The calls rows for full time: {rows: [{kind, cause, name, pts, text}], margin}.
## kind is "call" (one of ours), "other" (the rest of ours), "theirs" or
## "rest" (the players and the bounce). pts are whole points; a row worth 0 is
## left out. The rows' pts add up to `margin`. {} with no call on record.
static func calls(res: Dictionary, side: int) -> Dictionary:
	var score: Array = res.get("score", [])
	if score.size() < 2:
		return {}
	return calls_from(coach_rows(res, side), call_names(res, side), int(score[side]) - int(score[1 - side]))


## The same from a kept record's rows (MatchStory.record), so a match from
## the save tells its calls the same way.
static func calls_from(rows: Dictionary, names: Dictionary, margin: int) -> Dictionary:
	var mine: Dictionary = rows.get("mine", {})
	var theirs: Dictionary = rows.get("theirs", {})
	if mine.is_empty() and theirs.is_empty():
		return {}
	var order := mine.keys()
	order.sort_custom(func(a, b): return absf(float(mine[a])) > absf(float(mine[b])))
	var out := []
	var told := 0
	var other := 0.0
	for cause in order:
		var whole := roundi(float(mine[cause]))
		if out.size() < MAX_CALL_ROWS and whole != 0:
			out.append(_call_row("call", str(cause), str(names.get(cause, "Our " + str(CoachReport.IMPACT_LABELS.get(cause, cause)))), whole))
			told += whole
		else:
			other += float(mine[cause])
	var o := roundi(other)
	if o != 0:
		out.append(_call_row("other", "", "Our other calls", o))
		told += o
	var t := 0.0
	for cause in theirs:
		t -= float(theirs[cause])
	var tw := roundi(t)
	if tw != 0:
		out.append(_call_row("theirs", "", "Their calls", tw))
		told += tw
	if margin - told != 0:
		out.append(_call_row("rest", "", "The players and the bounce", margin - told))
	return {"rows": out, "margin": margin}


static func _call_row(kind: String, cause: String, name: String, pts: int) -> Dictionary:
	var n := absi(pts)
	var worth := ("%d point%s our way" if pts > 0 else "cost us %d point%s") % [n, "" if n == 1 else "s"]
	return {"kind": kind, "cause": cause, "name": name, "pts": pts, "text": "%s: %s." % [name, worth]}
