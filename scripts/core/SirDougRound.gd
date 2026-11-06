class_name SirDougRound
extends RefCounted
## Sir Doug Nicholls Round (row 75, T5.Q11b; Director Bible 2.73 and #128),
## behind the switch `sir_doug_round`.
##
## Each season one fixed mid-season round is Sir Doug Nicholls Round. It is a
## tribute, never a mechanic: it only labels a round the fixture already has.
## No bye, venue, home ground, morale, crowd or match result moves (how a club
## looks never touches the sim).
##
## A club with a bye in that round marks it the next round (2.73).
##
## Saved in GameState.sir_doug: {year, round, designs}. `designs` holds each
## club's design slot: a stored design id, or "none". No designs are in the game
## yet (the art is parked, 6.Q14: the First Nations artists are the director's
## to choose), so every slot is "none" and nothing is drawn. Nothing here makes
## a pattern or gives artwork a meaning. Once written, a season's record is
## read back from the save, so reloading cannot change it.

const SWITCH := "sir_doug_round"
## Round 11 (0-based 10): mid-season, inside the bye rounds (Season.BYE_FIRST
## to BYE_LAST).
const ROUND := 10
const NAME := "Sir Doug Nicholls Round"
## Short and factual. No claim about any guernsey or artwork.
const BLURB := "Pastor Sir Doug Nicholls, a Yorta Yorta man, played for Fitzroy in the 1930s and became the first Aboriginal person to be knighted. The round in his name celebrates Aboriginal and Torres Strait Islander players and their place in the game."
const NO_DESIGN := "none"


static func active(gs) -> bool:
	return Features.on(SWITCH) and gs != null and gs.season != null


## This season's record, written once per season (reloads read it back).
static func ensure(gs) -> Dictionary:
	if not active(gs):
		return {}
	var rec: Dictionary = gs.sir_doug if gs.sir_doug is Dictionary else {}
	if int(rec.get("year", 0)) == int(gs.season_year) and rec.has("round"):
		var designs: Dictionary = rec.get("designs", {})
		for c in gs.season.clubs:
			if not designs.has(str(c)):
				designs[str(c)] = NO_DESIGN
		rec["designs"] = designs
		return rec
	var designs := {}
	for c in gs.season.clubs:
		designs[str(c)] = NO_DESIGN
	rec = {"year": int(gs.season_year), "round": mini(ROUND, gs.season.fixture.size() - 1), "designs": designs}
	gs.sir_doug = rec
	return rec


## The round (0-based) of this season, or -1 with the switch off.
static func round_of(gs) -> int:
	var rec := ensure(gs)
	return int(rec.get("round", -1)) if not rec.is_empty() else -1


## The design slot of a club: a stored design id, or "none".
static func design_of(gs, code: String) -> String:
	var rec := ensure(gs)
	return str((rec.get("designs", {}) as Dictionary).get(code, NO_DESIGN))


## The clubs with a bye in round `ri` of the fixture.
static func byes_in(season, ri: int) -> Array:
	if season == null or ri < 0 or ri >= season.fixture.size():
		return []
	var playing := {}
	for m in season.fixture[ri]:
		playing[str(m["home"])] = true
		playing[str(m["away"])] = true
	var out := []
	for c in season.clubs:
		if not playing.has(str(c)):
			out.append(str(c))
	return out


## The round (0-based) in which `code` marks Sir Doug Nicholls Round: the round
## itself, or the first later round it plays after a bye in it (2.73; at 19 or
## 21 clubs two byes can fall back to back). -1 with the switch off, or when the
## club plays no later home-and-away round.
static func round_for(gs, code: String) -> int:
	var r := round_of(gs)
	if r < 0:
		return -1
	var ri := r
	while ri < gs.season.fixture.size() and byes_in(gs.season, ri).has(code):
		ri += 1
	return ri if ri < gs.season.fixture.size() else -1


## Is a home-and-away match in round `ri` between `home` and `away` part of
## Sir Doug Nicholls Round (for either club)?
static func marks(gs, ri: int, home: String, away: String) -> bool:
	if round_of(gs) < 0:
		return false
	return round_for(gs, home) == ri or round_for(gs, away) == ri


## The clubs marking the round late in round `ri` after their bye (2.73).
static func after_bye(gs, ri: int) -> Array:
	var r := round_of(gs)
	if r < 0 or ri <= r:
		return []
	var out := []
	for c in byes_in(gs.season, r):
		if round_for(gs, str(c)) == ri:
			out.append(str(c))
	return out
