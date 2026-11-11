class_name MedicalPanel
extends RefCounted
## The concussion medical panel (director, 2026-11-11: "if a player gets 5 or
## more concussions within a 5 year period, they should have to pass a medical
## retirement check"; "Flat odds each time"; "Straight after the fifth").
##
## Pure rules. The count is read from the career facts (CareerFacts.gd), which
## already keep every club's injuries with their season and kind, so nothing new
## is saved on the player: an injury an older save kept without its kind is not
## a concussion here, and a player with no facts has had none.
##
## Whenever a concussion leaves a player with SITS_AT or more inside the last
## YEARS seasons (this one and the four before), the panel sits that week: one
## seeded roll of its own against CLEAR_CHANCE. Cleared, he serves the normal
## protocol and plays on; every later concussion while the count stands is
## another sitting at the same odds. Not cleared, his career ends that week
## (GameState._medical_retire). Every club alike.

## The chance the panel clears him, the same at every sitting. The director's
## number to tune: every shown percentage is read from it.
const CLEAR_CHANCE := 0.5
## Concussions inside the window that make the panel sit.
const SITS_AT := 5
## The window, in seasons: this one and the YEARS - 1 before it.
const YEARS := 5
## The count is shown on a player from here: two short of the panel.
const SHOWN_FROM := 3


## His diagnosed concussions in `year` and the YEARS - 1 seasons before it.
static func count(store: Dictionary, id: String, year: int) -> int:
	var n := 0
	var rows = store.get(id, [])
	if rows is Array:
		for r in rows:
			if str(r[CareerFacts.K]) == "injury" and str(r[CareerFacts.OUT]) == "concussion" \
					and int(r[CareerFacts.Y]) > year - YEARS and int(r[CareerFacts.Y]) <= year:
				n += 1
	return n


## Every concussion on his record, whenever it was: what makes each sitting's
## roll its own.
static func count_ever(store: Dictionary, id: String) -> int:
	var n := 0
	var rows = store.get(id, [])
	if rows is Array:
		for r in rows:
			if str(r[CareerFacts.K]) == "injury" and str(r[CareerFacts.OUT]) == "concussion":
				n += 1
	return n


## Does a concussion that leaves him on `n` in the window bring the panel?
static func sits(n: int) -> bool:
	return n >= SITS_AT


## One sitting: is he cleared? Its own seeded roll (the career, the player, the
## season and which concussion of his career this is), so the same save gives
## the same answer and no match, injury or draft dice are touched.
static func cleared(career_seed: int, id: String, year: int, nth: int) -> bool:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("%d|medical_panel|%s|%d|%d" % [career_seed, id, year, nth])
	return rng.randf() < CLEAR_CHANCE


## The chance of being cleared, as the whole percentage every line shows.
static func clear_pct() -> int:
	return int(round(CLEAR_CHANCE * 100.0))


## "4 concussions in 5 years": the count on a list row.
static func count_text(n: int) -> String:
	return "%d concussion%s in %d years" % [n, "" if n == 1 else "s", YEARS]


## The player sheet's line once the count matters (SHOWN_FROM or more), "" before.
static func warning(n: int) -> String:
	if n < SHOWN_FROM:
		return ""
	if n >= SITS_AT:
		return "%s. Another one and the medical panel sits again: %d%% chance of being cleared to play on." % [
				count_text(n), clear_pct()]
	var more := SITS_AT - n
	return "%s. %s more and the medical panel sits: %d%% chance of being cleared to play on." % [
			count_text(n), "One" if more == 1 else "Two", clear_pct()]


## The week's result for the coach's own player: {"name", "count", "cleared", "pct"}.
static func result_line(row: Dictionary) -> String:
	var who := str(row.get("name", "The player"))
	var n := int(row.get("count", SITS_AT))
	var pct := int(row.get("pct", clear_pct()))
	if bool(row.get("cleared", false)):
		return "%s had his %s concussion in %d years and the medical panel sat. The panel cleared him to play on (%d%% chance). Another concussion and it sits again." % [
				who, Almanac.ordinal(n), YEARS, pct]
	return "%s had his %s concussion in %d years and the medical panel sat. The panel did not clear him (%d%% chance of being cleared): his career is over and your list is a player short." % [
			who, Almanac.ordinal(n), YEARS, pct]


## The same, short enough to sit under the week's injuries.
static func result_short(row: Dictionary) -> String:
	return "%s %s (%d%% chance of being cleared)" % [str(row.get("name", "The player")),
			"cleared to play on" if bool(row.get("cleared", false)) else "not cleared, career over",
			int(row.get("pct", clear_pct()))]


## A rival's sitting, for league news.
static func league_line(row: Dictionary, club_name: String) -> String:
	var who := str(row.get("name", "A player"))
	var n := int(row.get("count", SITS_AT))
	if bool(row.get("cleared", false)):
		return "%s (%s) has been cleared by the medical panel to play on after his %s concussion in %d years." % [
				who, club_name, Almanac.ordinal(n), YEARS]
	return "%s (%s) has played his last game: the medical panel did not clear him after his %s concussion in %d years." % [
			who, club_name, Almanac.ordinal(n), YEARS]

