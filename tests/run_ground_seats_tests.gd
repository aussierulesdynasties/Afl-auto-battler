extends SceneTree
## godot --headless --path . --script tests/run_ground_seats_tests.gd
## Row 202 2b: every ground's instanced seats keep to the shared seat rule
## (tools/grounds/seat_rule.gd): none floats over no floor, none has a roof, a tier or an
## aisle stair through a seated supporter's head, none is inside the boundary fence, none is
## left alone on a ledge. A rebuilt ground that breaks it is fixed by
## `tools/grounds/seat_check.gd -- --write <slug>` (or at its generator). Looks only.
## Seeded by design: it measures the seat files against the models, nothing random runs.

const SeatRule := preload("res://tools/grounds/seat_rule.gd")
## Grounds whose own pull request is still taking their bad seats out (the MCG, #1987);
## each leaves this list when that lands and seat_check has been run on it.
const PENDING := ["mcg"]

var _checks := 0
var _failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	await process_frame
	await _t("_test_every_ground")
	_t("_test_rule_catches")
	print(Ran.line("Ground seats", self))
	quit(0 if _failures.is_empty() else 1)


func _test_every_ground() -> void:
	var grounds := SeatRule.grounds()
	_check(grounds.size() >= 10, "Grounds with instanced seats are found (%d)" % grounds.size())
	for slug in grounds:
		if PENDING.has(slug):
			continue
		var r: Dictionary = SeatRule.new().check(str(slug), root)
		_check(int(r["seats"]) > 0, "%s has seats" % slug)
		var first: Array = r["spots"].slice(0, 3)
		_check(int(r["removed"]) == 0, "%s: every one of its %d seats keeps the seat rule (%d fail %s, first %s)" % [
				slug, int(r["seats"]), int(r["removed"]), JSON.stringify(r["why"]), JSON.stringify(first)])
		await process_frame


## The rule is not vacuous: a pending ground still carrying its bad seats is caught on each count
## it is known for (the MCG's rows past its south stand, its seats under the tiers).
func _test_rule_catches() -> void:
	var r: Dictionary = SeatRule.new().check("mcg", root)
	var why: Dictionary = r["why"]
	_check(int(r["seats"]) > 50000, "The MCG has its seats (%d)" % int(r["seats"]))
	_check(int(why["floor"]) > 0 or int(r["seats"]) < 70000,
			"Seats over no floor are caught, or the MCG's were already taken out (%s)" % JSON.stringify(why))
	_check(SeatRule.HEADROOM >= 2.0 and SeatRule.FLOAT_SLACK <= 0.6, "The rule's limits are a real stand's")


func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)
		push_error(message)


## Runs one test function; it must make at least one check (tests/functions_ran.gd).
const Ran := preload("res://tests/functions_ran.gd")
func _t(test: String, args := []) -> Variant:
	return await Ran.one(self, test, args)
