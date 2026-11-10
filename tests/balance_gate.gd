## Balance-threshold checks wait for the balance pass (director 2026-11-10:
## "we can rigorously audit and balance after the game is fully featured").
## A gated check still runs and prints BALANCE_DEFERRED| when it misses, so
## the drift stays visible in the logs; it fails the suite only when the
## balance pass sets BALANCE_CHECKS=1 (TODO section Z).
extends RefCounted

static func on() -> bool:
	return OS.get_environment("BALANCE_CHECKS") == "1"

## Pass `ok` through to the suite's own check when the balance pass is on;
## otherwise log a miss and let it pass.
static func held(ok: bool, message: String) -> bool:
	if not ok:
		print("BALANCE_DEFERRED| " + message)
	return ok or not on()
