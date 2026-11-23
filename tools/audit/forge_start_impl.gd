extends RefCounted
## Club Forge club on a real-lists start: how strong is it when it enters,
## and how does it climb? (bug bash 2026-11-23: an AI-run Forge club was the
## best-rated side in the league in its first season.) Autopilot careers:
## the real 2026 lists, a created club, you coach `club`, every draft and
## off-season run by the rival AI.
## Lines:
##   ENTRY  seed year | the Forge club's best 22, its rank, what its list is made of
##   TOP    seed year | its ten best players at entry, where each came from
##   FORGE  seed year clubyear | ladder place, wins, strength rank
##   TAS    seed year clubyear | Tasmania (enters 2028 on the same signings)
##   SUMMARY by club and club year over all careers.
## Args: seeds (comma list) club seasons (default 301 RIC 6).
## godot --headless --path . --script tools/audit/run_audit.gd -- forge_start_impl 301,302 RIC 6

const CODE := "COB"

var rows := []


func _spec() -> Dictionary:
	return {"name": "Coburg", "short": "Lions", "code": CODE, "location": "coburg",
			"primary": "#13234B", "secondary": "#C8102E", "accent": "#F5F5F5", "design": "sash", "kit": "p/s/a"}


func _top(list: Array, n: int) -> Array:
	var ovr := list.duplicate()
	ovr.sort_custom(func(a, b): return int(a["overall"]) > int(b["overall"]))
	return ovr.slice(0, mini(n, ovr.size()))


func _strength(list: Array) -> float:
	var t := 0.0
	for p in _top(list, 22):
		t += float(p["overall"])
	return t / 22.0


func _rank(lists: Dictionary) -> int:
	var mine := _strength(lists[CODE])
	var r := 1
	for c in lists:
		if str(c) != CODE and _strength(lists[c]) > mine:
			r += 1
	return r


func _mean(lists: Dictionary) -> float:
	var t := 0.0
	var n := 0
	for c in lists:
		if str(c) != CODE:
			t += _strength(lists[c])
			n += 1
	return t / maxf(1.0, float(n))


## The ladder's Rating column (GameState.club_strength, the best 18 as picked)
## and the Forge club's place on it.
func _rating_rank(lists: Dictionary) -> Array:
	var mine: float = GameState.club_strength(CODE)
	var r := 1
	var top := 0.0
	for c in lists:
		var v: float = GameState.club_strength(str(c))
		top = maxf(top, v) if str(c) != CODE else top
		if str(c) != CODE and v > mine:
			r += 1
	return [mine, r, top]


func _best(lists: Dictionary) -> float:
	var b := 0.0
	for c in lists:
		if str(c) != CODE:
			b = maxf(b, _strength(lists[c]))
	return b


func _origin(p: Dictionary, st: Dictionary) -> String:
	var id := str(p["id"])
	if id.begins_with("FND_"):
		return "state"
	if (st.get("fa_signings", []) as Array).has(id):
		return "fa"
	if (st.get("signings", []) as Array).has(id):
		return "rival"
	if p.has("joined"):
		return "trade"
	if str(p.get("src", "")) == "U18" or p.has("pick"):
		return "draft"
	return "other"


func _entry(seed: int) -> void:
	var lists: Dictionary = GameState.season.lists
	var arr: Array = lists[CODE]
	var st: Dictionary = GameState.expansion.get(CODE, {})
	var counts := {}
	var in22 := {}
	var top := _top(arr, 22)
	for p in arr:
		var o := _origin(p, st)
		counts[o] = int(counts.get(o, 0)) + 1
	for p in top:
		var o := _origin(p, st)
		in22[o] = int(in22.get(o, 0)) + 1
	var rr := _rating_rank(lists)
	print("RATING %d %d | ladder Rating %.1f, rank %d (best rival %.1f)" % [seed, GameState.season_year, rr[0], rr[1], rr[2]])
	print("ENTRY %d %d | best 22 %.1f (league mean %.1f, best rival %.1f) | rank %d of %d | list %d %s | best 22 from %s | payroll %.2f of cap" % [
			seed, GameState.season_year, _strength(arr), _mean(lists), _best(lists), _rank(lists), lists.size(),
			arr.size(), str(counts), str(in22), float(Contracts.payroll(arr)) / maxf(1.0, float(GameState.salary_cap))])
	var bits := PackedStringArray()
	for p in _top(arr, 12):
		bits.append("%s %d %.0fy %s" % [GameDB.player_display_name(p), int(p["overall"]), float(p.get("age", 0)), _origin(p, st)])
	print("TOP %d %d | %s" % [seed, GameState.season_year, ", ".join(bits)])


## Tasmania enters in 2028 on the same state-league signings (and its own
## approaches and traded picks): one line a season once it plays.
func _tas_line(seed: int) -> void:
	var lists: Dictionary = GameState.season.lists
	if not lists.has("TAS"):
		return
	var table := GameState.season.ladder_sorted()
	var cy := GameState.season_year - GameDB.enter_year("TAS") + 1
	for i in range(table.size()):
		if str(table[i]["code"]) != "TAS":
			continue
		var mine := _strength(lists["TAS"])
		var rk := 1
		var t := 0.0
		for c in lists:
			if str(c) != "TAS":
				t += _strength(lists[c])
				if _strength(lists[c]) > mine:
					rk += 1
		rows.append({"seed": seed, "cy": cy, "pos": i + 1, "n": table.size(), "w": int(table[i]["w"]), "rank": rk,
				"str": mine - t / float(lists.size() - 1), "rr": 0, "club": "TAS"})
		print("TAS %d %d year %d | ladder %d of %d | %d-%d | strength rank %d | best 22 %.1f" % [
				seed, GameState.season_year, cy, i + 1, table.size(), int(table[i]["w"]), int(table[i]["l"]), rk, mine])


func _season_end(seed: int, cy: int) -> void:
	_tas_line(seed)
	var table := GameState.season.ladder_sorted()
	var lists: Dictionary = GameState.season.lists
	for i in range(table.size()):
		if str(table[i]["code"]) != CODE:
			continue
		var row: Dictionary = table[i]
		var rk := _rank(lists)
		var rr := _rating_rank(lists)
		rows.append({"seed": seed, "cy": cy, "pos": i + 1, "n": table.size(), "w": int(row["w"]), "rank": rk,
				"str": _strength(lists[CODE]) - _mean(lists), "rr": int(rr[1]), "club": CODE})
		print("FORGE %d %d year %d | ladder %d of %d | %d-%d | strength rank %d | Rating rank %d (%.1f) | best 22 %.1f (mean %.1f)" % [
				seed, GameState.season_year, cy, i + 1, table.size(), int(row["w"]), int(row["l"]), rk, int(rr[1]), float(rr[0]),
				_strength(lists[CODE]), _mean(lists)])


func _ai_finish(draft: Draft) -> void:
	var guard := 0
	draft.auto_until_user_turn()
	while not draft.is_finished() and guard < 8000:
		guard += 1
		var cand := draft._best_ai_pick(draft.current_club())
		if cand.is_empty() or not draft._draft_pick(draft.current_club(), cand):
			draft._skip_current_pick()
		draft.auto_until_user_turn()


func _career(seed: int, club: String, seasons: int) -> void:
	GameState.reset()
	GameState.autosave_enabled = false
	GameState.career_seed = seed
	GameState.replay_seed = seed
	var problem: String = GameState.create_club(_spec())
	if problem != "":
		push_error(problem)
		return
	GameState.begin_real_lists()
	GameState.choose_real_club(club)
	_ai_finish(GameState.draft)
	GameState.finish_intake_draft()
	for s in range(seasons):
		if s == 0:
			_entry(seed)
		while not GameState.season.is_season_over():
			GameState.advance()
		_season_end(seed, s + 1)
		if s == seasons - 1:
			break
		GameState.open_offseason()
		if GameState.begin_intake_draft():
			_ai_finish(GameState.draft)
			GameState.finish_intake_draft()
		else:
			GameState.start_next_season()


func _summary() -> void:
	for club in [CODE, "TAS"]:
		_summary_of(club)


func _summary_of(club: String) -> void:
	var by := {}
	for r in rows:
		if str(r["club"]) != club:
			continue
		if not by.has(r["cy"]):
			by[r["cy"]] = []
		(by[r["cy"]] as Array).append(r)
	var ks := by.keys()
	ks.sort()
	for cy in ks:
		var arr: Array = by[cy]
		var pos := []
		var w := 0.0
		var rk := 0.0
		var sd := 0.0
		var rrk := 0.0
		for r in arr:
			rrk += float(r["rr"])
			pos.append(int(r["pos"]))
			w += float(r["w"])
			rk += float(r["rank"])
			sd += float(r["str"])
		pos.sort()
		var m := 0.0
		for p in pos:
			m += float(p)
		var n := float(arr.size())
		print("SUMMARY %s year %d | n %d | ladder mean %.1f places %s | wins %.1f | strength rank %.1f | Rating rank %.1f | best 22 vs league mean %+.1f" % [
				club, int(cy), arr.size(), m / n, str(pos), w / n, rk / n, rrk / n, sd / n])


func run() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := [301]
	var club := "RIC"
	var seasons := 6
	if args.size() > 1:
		seeds = []
		for s in str(args[1]).split(","):
			seeds.append(int(s))
	if args.size() > 2:
		club = str(args[2])
	if args.size() > 3:
		seasons = int(args[3])
	for s in seeds:
		_career(int(s), club, seasons)
	_summary()
