class_name LeagueNews
extends RefCounted
## The league news layer (row 76, T5.Q11d): items the save already proves,
## added to the league news feed (GameState.add_news) after each home-and-away
## round, and shown on the existing front page (NewsFront). Switch
## "league_news"; off, nothing is written.
##
##   streak   a club's winning run reaches 5, 7, 10, 13, 16 or 19 straight this
##            season, or a run of 5 or more ends (season.results).
##   ladder   a new club on top of the ladder after a round, from Round 3 on
##            (the table from season.results, the AFL order: points,
##            percentage, then points for).
##
## Reads only: no rating, morale, list or match changes. Award winners,
## milestones, club records (the almanac) and big games are told elsewhere
## already; each fact has one place.

const STREAK_MARKS := [5, 7, 10, 13, 16, 19]
## A run this long is news when it ends.
const STREAK_ENDS := 5
## The first round after which the top of the ladder is news.
const LADDER_FROM := 3


static func on() -> bool:
	return Features.on("league_news")


## After a round has been recorded in season.results (GameState._after_round).
static func after_round(gs, results: Array) -> void:
	if not on() or gs.season == null or str(gs.last_phase) != "regular" or results.is_empty():
		return
	var rounds: Array = gs.season.results
	if rounds.is_empty():
		return
	for line in streak_lines(rounds):
		gs.add_news("streak", line)
	var top := ladder_line(rounds)
	if top != "":
		gs.add_news("ladder", top)


## A club's results in `rounds`, oldest first: [{"r": "W"/"L"/"D", "opp": code}].
static func club_run(rounds: Array, code: String) -> Array:
	var out := []
	for rnd in rounds:
		for res in rnd:
			var side := -1
			if str(res.get("home", "")) == code:
				side = 0
			elif str(res.get("away", "")) == code:
				side = 1
			if side < 0:
				continue
			var s: Array = res.get("score", [0, 0])
			var r := "D"
			if int(s[side]) > int(s[1 - side]):
				r = "W"
			elif int(s[side]) < int(s[1 - side]):
				r = "L"
			out.append({"r": r, "opp": str(res["away"] if side == 0 else res["home"])})
	return out


## Wins in a row at the end of `run`, before index `upto` (exclusive).
static func wins_in_a_row(run: Array, upto: int) -> int:
	var n := 0
	var i := upto - 1
	while i >= 0 and str(run[i]["r"]) == "W":
		n += 1
		i -= 1
	return n


## The newest round's streak lines, one per club at most, in the round's order.
static func streak_lines(rounds: Array) -> Array:
	var out := []
	var last: Array = rounds[rounds.size() - 1]
	var codes := []
	for res in last:
		codes.append(str(res.get("home", "")))
		codes.append(str(res.get("away", "")))
	for code in codes:
		var run := club_run(rounds, code)
		if run.is_empty():
			continue
		var now: Dictionary = run[run.size() - 1]
		if str(now["r"]) == "W":
			var n := wins_in_a_row(run, run.size())
			if STREAK_MARKS.has(n):
				out.append("%s have won %d in a row after beating %s." % [
						GameDB.club_name(code), n, GameDB.club_name(str(now["opp"]))])
		else:
			var was := wins_in_a_row(run, run.size() - 1)
			if was >= STREAK_ENDS:
				out.append("%s's run of %d straight wins ended against %s." % [
						GameDB.club_name(code), was, GameDB.club_name(str(now["opp"]))])
	return out


## The ladder over `rounds`: [{code, w, l, d, pf, pa, pts, pct}], top first,
## sorted as Season.ladder_sorted (points, percentage, points for).
static func table(rounds: Array) -> Array:
	var rows := {}
	for rnd in rounds:
		for res in rnd:
			var s: Array = res.get("score", [0, 0])
			for side in [0, 1]:
				var code := str(res["home"] if side == 0 else res["away"])
				if not rows.has(code):
					rows[code] = {"code": code, "w": 0, "l": 0, "d": 0, "pf": 0, "pa": 0}
				var row: Dictionary = rows[code]
				row["pf"] = int(row["pf"]) + int(s[side])
				row["pa"] = int(row["pa"]) + int(s[1 - side])
				if int(s[side]) > int(s[1 - side]):
					row["w"] = int(row["w"]) + 1
				elif int(s[side]) < int(s[1 - side]):
					row["l"] = int(row["l"]) + 1
				else:
					row["d"] = int(row["d"]) + 1
	var out := []
	for code in rows:
		var row: Dictionary = rows[code]
		row["pts"] = int(row["w"]) * 4 + int(row["d"]) * 2
		row["pct"] = (100.0 * int(row["pf"]) / int(row["pa"])) if int(row["pa"]) > 0 else 0.0
		out.append(row)
	out.sort_custom(func(a, b):
		if a["pts"] != b["pts"]:
			return int(a["pts"]) > int(b["pts"])
		if not is_equal_approx(a["pct"], b["pct"]):
			return a["pct"] > b["pct"]
		return int(a["pf"]) > int(b["pf"]))
	return out


## "<Club> are on top of the ladder after Round N: W wins and a percentage of P." when the
## newest round put a different club on top; "" otherwise or before LADDER_FROM.
static func ladder_line(rounds: Array) -> String:
	if rounds.size() < LADDER_FROM:
		return ""
	var before := table(rounds.slice(0, rounds.size() - 1))
	var after := table(rounds)
	if before.is_empty() or after.is_empty():
		return ""
	var top: Dictionary = after[0]
	if str(top["code"]) == str((before[0] as Dictionary)["code"]):
		return ""
	var wins := int(top["w"])
	var newest: Array = rounds[rounds.size() - 1]
	var label := "Round %d" % rounds.size()
	if not newest.is_empty():
		label = str((newest[0] as Dictionary).get("label", label))
	return "%s are on top of the ladder after %s: %d win%s and a percentage of %.1f." % [
			GameDB.club_name(str(top["code"])), label, wins, "" if wins == 1 else "s", float(top["pct"])]
