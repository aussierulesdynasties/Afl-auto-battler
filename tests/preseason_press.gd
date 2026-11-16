extends RefCounted
## Tests: press on through the pre-season (rule 69a) as a coach who takes what
## is there: the meetings done as they stand, the fitness plan the club already
## runs, and each week the first action open (the booked running while it is
## owed, then drilling the plan the side plays). Suites that are not about the
## pre-season's own choices use this to get past them.


## Answer the stops that wait on a choice: the meetings, the plan, the week.
static func answer() -> void:
	if GameState.preseason_stop() == "meetings":
		GameState.preseason_meetings_done()
	if GameState.preseason_stop() == "plan":
		GameState.set_preseason_plan(GameState.fitness_plan(GameState.my_club))
	if GameState.preseason_stop() == "week" and GameState.preseason_next().is_empty():
		var open := GameState.preseason_actions()
		if not open.is_empty():
			GameState.set_preseason_action(str(open[0]))


## preseason_advance with the choices above made first.
static func advance() -> String:
	answer()
	return GameState.preseason_advance()


## Press on until the pre-season waits at `stop` (or is over). True when it is there.
static func to(stop: String, guard := 24) -> bool:
	var n := 0
	while GameState.preseason_active() and GameState.preseason_stop() != stop and n < guard:
		n += 1
		advance()
	return GameState.preseason_stop() == stop


## Press on until `week` weeks are done (or the pre-season is over).
static func to_week(week: int, guard := 24) -> void:
	var n := 0
	while GameState.preseason_active() and GameState.preseason_week() < week and n < guard:
		n += 1
		advance()
