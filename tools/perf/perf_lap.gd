extends RefCounted
## Step timer for the bench of weeks (T8.Q20). tools/perf/lap_instrument.py
## puts one at the top of each listed function of a throwaway bench tree and a
## lap() before each of its top-level statements: the time from one lap to the
## next goes to that statement, and the last one closes when the function
## returns. Never used by the game; reads no RNG, so results are unchanged.

static var totals := {}   # "Fn | statement" -> [ms, calls]
static var order := []

var _fn := ""
var _label := ""
var _t := 0


func _init(fn: String) -> void:
	_fn = fn


func lap(label: String) -> void:
	var now := Time.get_ticks_usec()
	_close(now)
	_label = label
	_t = now


func _close(now: int) -> void:
	if _label == "":
		return
	var key := "%s | %s" % [_fn, _label]
	if not totals.has(key):
		totals[key] = [0.0, 0]
		order.append(key)
	totals[key][0] += (now - _t) / 1000.0
	totals[key][1] += 1
	_label = ""


func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE:
		_close(Time.get_ticks_usec())


static func dump(prefix := "LAP") -> void:
	for key in order:
		var v: Array = totals[key]
		print("%s %10.1f ms %7d x  %s" % [prefix, v[0], v[1], key])
