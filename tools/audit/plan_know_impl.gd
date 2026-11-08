extends RefCounted
## What knowing a plan is worth on the margin: the paired measure behind the seeded check in
## tests/test_plan_know.gd. Measurement only; no balance is changed.
##   gh workflow run audit.yml --ref <branch> -f impl=plan_know_impl -f env="PN=200"
## Fremantle run the contest plan against Melbourne on the same seeds (900 + i), once knowing it
## fully and once barely; each line is the margin with it known minus the margin barely known.
## Output: P|i|difference per match, then the mean, the standard deviation, the standard error and
## the mean over the first 24 and 48 seeds.


func _sim(known: Dictionary, seed_: int) -> MatchSim:
	var a := Squad.new("A", GameDB.club_list("FRE"), true, "FRE")
	var b := Squad.new("B", GameDB.club_list("MEL"), false, "MEL")
	a.plan_know = known
	b.plan_know = {}
	var sim := MatchSim.new(a, b, seed_)
	sim.set_tactics(0, {"gameplan": "contest"})
	sim.set_tactics(1, {"gameplan": "balanced"})
	return sim


func _margin(r: Dictionary) -> float:
	return float(int(r["score"][0]) - int(r["score"][1]))


func _first(vals: Array[float], k: int) -> float:
	var sum := 0.0
	for i in range(mini(k, vals.size())):
		sum += vals[i]
	return sum / float(maxi(1, mini(k, vals.size())))


func run() -> void:
	PreSeason.reload()
	var barely := PreSeason.familiar_mult(0)
	var n := int(OS.get_environment("PN")) if OS.get_environment("PN") != "" else 200
	var vals: Array[float] = []
	for i in range(n):
		var d := _margin(_sim({}, 900 + i).run()) - _margin(_sim({"contest": barely}, 900 + i).run())
		vals.append(d)
		print("P|%d|%.0f" % [i, d])
	var m := _first(vals, n)
	var ss := 0.0
	for v in vals:
		ss += (v - m) * (v - m)
	var sd := sqrt(ss / float(maxi(1, n - 1)))
	print("PLAN_KNOW n=%d mean=%.2f sd=%.2f se=%.2f first24=%.2f first48=%.2f" % [n, m, sd, sd / sqrt(float(n)), _first(vals, 24), _first(vals, 48)])
