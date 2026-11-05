extends RefCounted
## tools/balance.sh match on GitHub's runner (audit.yml), for samples too big for
## this PC: plays seeds from..from+count exactly as balance_worker.gd does (same
## lists, same match seeds, so a GitHub slice pairs with a local one) and prints
## each match as "BAL <json>". Measurement only.
##
##   gh workflow run audit.yml --ref <branch> -f impl=balance_match_impl \
##       -f args="0 1000" -f env="BAL_ON=momentum_runaway"
##   gh run download <id> -n audit-balance_match_impl -D <dir>
##   python tools/balance/from_audit.py --run <run dir> --arm b <dir>/audit.log ...
##
## Env: BAL_ON / BAL_OFF (Features switches, comma-separated), BAL_WEATHER,
## BAL_SET (MatchSim vars, name=value,...).


func run() -> void:
	var a := OS.get_cmdline_user_args()
	var from := int(a[1]) if a.size() > 1 else 0
	var count := int(a[2]) if a.size() > 2 else 100
	var on := OS.get_environment("BAL_ON").split(",", false)
	var off := OS.get_environment("BAL_OFF").split(",", false)
	var weather := OS.get_environment("BAL_WEATHER")
	var body = load("res://tools/balance/balance_body.gd").new()
	var code: int = body.play(from, count, "user://balance_audit.jsonl", on, off,
			weather if weather != "" else "perfect",
			body.parse_sets(OS.get_environment("BAL_SET")), true)
	print("SUMMARY balance_match from %d count %d on %s set %s code %d" % [
			from, count, ",".join(on), OS.get_environment("BAL_SET"), code])
