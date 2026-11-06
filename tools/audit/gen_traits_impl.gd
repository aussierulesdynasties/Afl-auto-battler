extends RefCounted
## Generated players' traits against the real players' (row 104, 4.Q10): per trait, the
## share of the real 2026 list players who carry it, and the share of generated players
## who do - at the draft, and grown GROW seasons by the development rules (no matches,
## no training, no league re-anchor). Both arms in one run: the gen_traits switch off
## (as main) and on, on the same classes.
##
##   godot --headless --path . --script tools/audit/run_audit.gd -- gen_traits_impl [classes] [grow]
##   (default 30 classes from 2027, career seed 4242 + year; grow 5)
##
## Lines:
##   REAL <trait> <pct> (<n>/<N>)                     every real listed player
##   GEN <arm> <trait> draft <pct> grown <pct> matched <pct> (<n>/<N>)
##     "matched" weights the grown players' share in each 4-point OVR band by the real
##     players' OVR mix, so it is the rate a generated player carries at a real player's
##     level: the in-career league is re-anchored to the 2026 OVR spread every rollover,
##     so this is what a league of grown generated players would show.
##   RATE <trait> | real x | off grown y matched z | on grown y matched z   (the table)
## Measurement only: it never changes a rule.
const TRAITS := ["bull", "ball_magnet", "ruck_king", "aerial", "crumber", "sharpshooter",
		"playmaker", "interceptor", "lockdown", "def_forward", "engine", "big_game", "hothead"]
const BAND := 4


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var classes := int(args[1]) if args.size() > 1 else 30
	var grow := int(args[2]) if args.size() > 2 else 5
	var real := _real_players()
	var real_bands := _bands(real)
	var real_share := {}
	for t in TRAITS:
		var n := 0
		for p in real:
			n += 1 if Traits.of(p).has(t) else 0
		real_share[t] = 100.0 * n / maxi(1, real.size())
		print("REAL %-12s %5.1f%% (%d/%d)" % [t, real_share[t], n, real.size()])
	var arms := {}
	for arm in ["off", "on"]:
		Features.set_on("gen_traits", arm == "on")
		Prospects.forget_cache()
		var drafted := []
		var grown := []
		for y in range(2027, 2027 + classes):
			for p in Prospects.generate_class(y, 4242 + y):
				drafted.append(p.duplicate(true))
				var q: Dictionary = p
				for k in range(1, grow + 1):
					Prospects.age_player(q, y + k)
				grown.append(q)
		var ovr0 := 0.0
		var ovr1 := 0.0
		for i in range(drafted.size()):
			ovr0 += float(drafted[i]["overall"])
			ovr1 += float(grown[i]["overall"])
		print("GEN %s %d players: mean OVR at the draft %.1f, %d seasons on %.1f (real %.1f)" % [arm,
				drafted.size(), ovr0 / drafted.size(), grow, ovr1 / grown.size(), _mean_ovr(real)])
		var row := {}
		for t in TRAITS:
			var nd := 0
			var ng := 0
			for i in range(drafted.size()):
				nd += 1 if Traits.of(drafted[i]).has(t) else 0
				ng += 1 if Traits.of(grown[i]).has(t) else 0
			var m := _matched(grown, t, real_bands, real.size())
			row[t] = [100.0 * nd / drafted.size(), 100.0 * ng / grown.size(), m]
			print("GEN %s %-12s draft %5.1f%% grown %5.1f%% matched %5.1f%% (%d/%d)" % [arm, t,
					row[t][0], row[t][1], m, ng, grown.size()])
		arms[arm] = row
	Features.clear("gen_traits")
	Prospects.forget_cache()
	print("RATE | trait | real | off: draft, grown, matched | on: draft, grown, matched")
	for t in TRAITS:
		var o: Array = arms["off"][t]
		var n: Array = arms["on"][t]
		print("RATE | %s | %.1f%% | %.1f%%, %.1f%%, %.1f%% | %.1f%%, %.1f%%, %.1f%%" % [t, real_share[t],
				o[0], o[1], o[2], n[0], n[1], n[2]])


## Every real (curated) player on the 2026 lists.
func _real_players() -> Array:
	var out := []
	for c in GameDB.club_order:
		for p in GameDB.club_list(c):
			if not bool(p.get("generated", false)):
				out.append(p)
	return out


func _band(p: Dictionary) -> int:
	return int(p.get("overall", 0)) / BAND


func _bands(players: Array) -> Dictionary:
	var out := {}
	for p in players:
		out[_band(p)] = int(out.get(_band(p), 0)) + 1
	return out


func _mean_ovr(players: Array) -> float:
	var s := 0.0
	for p in players:
		s += float(p.get("overall", 0))
	return s / maxi(1, players.size())


## The grown players' share of trait t, each OVR band weighted by the real players in it
## (bands with no grown player are left out and the weights renormalised).
func _matched(grown: Array, t: String, real_bands: Dictionary, _n: int) -> float:
	var have := {}
	var tot := {}
	for q in grown:
		var b := _band(q)
		tot[b] = int(tot.get(b, 0)) + 1
		if Traits.of(q).has(t):
			have[b] = int(have.get(b, 0)) + 1
	var w := 0.0
	var s := 0.0
	for b in real_bands:
		if int(tot.get(b, 0)) == 0:
			continue
		w += float(real_bands[b])
		s += float(real_bands[b]) * float(have.get(b, 0)) / float(tot[b])
	return 100.0 * s / maxf(1.0, w)
