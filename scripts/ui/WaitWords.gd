class_name WaitWords
extends RefCounted
## The words for taking a club that joins after the real-lists start (director,
## 2026-11-09: picking Tasmania plays 2027 without you and starts you in 2028).
## One wording for both ways in: the club's card on Choose your club
## (DraftScene) and the 2028 start on the New career year step (Main, TODO row
## 142).


## The seasons played without you before `code` joins: "2027", or "2027 to 2029".
## `start` is the career's first season, today's (2027) when the career is not
## set up yet: the year step speaks before the 2026 lists are loaded.
static func years_without(code: String, start := 0) -> String:
	var first := _first(start)
	var year := GameDB.enter_year(code) if start == 0 else GameDB.data_enter_year(code)
	if year - 1 == first:
		return "%d" % first
	return "%d to %d" % [first, year - 1]


## What waiting for `code` costs and gives, one sentence a line.
static func lines(code: String, start := 0) -> Array:
	var year := GameDB.enter_year(code) if start == 0 else GameDB.data_enter_year(code)
	var name_ := GameDB.club_name(code)
	var plays := "plays" if year - 1 == _first(start) else "play"
	return [
		"%s join the league in %d, so your first season is %d." % [name_, year, year],
		"%s %s out without you. Their staff sign %d state-league players, chase out-of-contract players at rival clubs and trade picks 5, 7, 11 and 13 for senior players." % [
			years_without(code, start), plays, Expansion.FOUNDATION_SIZE],
		"You take over at the %d National Draft with picks 1, 3 and 9, the first pick of each later round, and any players from their academy." % (year - 1),
	]


static func _first(start: int) -> int:
	return start if start > 0 else GameDB.START_YEAR
