extends RefCounted
## Payroll against the cap for every club at a real-lists start (bug bash
## 2026-11-23). Args: starts (comma-separated, default 2010).

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var starts := str(args[1]) if args.size() > 1 else "2010"
	for st in starts.split(",", false):
		var gs := GameDB.get_tree().root.get_node("GameState")
		gs.autosave_enabled = false
		gs.reset(str(st))
		gs.career_seed = 1
		gs.replay_seed = 1
		gs.begin_real_lists()
		var order: Array = GameDB.club_order
		gs.choose_real_club(str(order[order.size() - 1]))
		gs.draft.start_for_user("")
		gs.finish_intake_draft()
		var rows := []
		for code in gs.season.lists:
			var list: Array = gs.season.lists[code]
			var top := 0
			var sum_ovr := 0
			for p in list:
				sum_ovr += int(p.get("overall", 0))
				top = maxi(top, int(p.get("salary", 0)))
			rows.append("%s pay %.2fm (%.0f%%) list %d meanOVR %.1f top %dk" % [code,
					Contracts.payroll(list) / 1e6, 100.0 * Contracts.payroll(list) / gs.cap_for(str(code)),
					list.size(), float(sum_ovr) / maxf(1, list.size()), top / 1000])
		print("START %s cap %d | %s" % [st, gs.salary_cap, " ; ".join(rows)])
