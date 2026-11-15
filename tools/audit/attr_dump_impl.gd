extends RefCounted
## Every real player's attributes as the game rates them, one parseable line each:
##   ATTR start|club|name|role|overall|disposal|contested|marking|pressure|intercept|carry|goalkicking|accuracy|creating|ruck
## For before/after comparisons of a ratings change (director 2026-11-15: every
## rating compared with players in his own position). Reads; changes nothing.
## Args: starts (default 2026 1990).

const KEYS := ["disposal", "contested", "marking", "pressure", "intercept", "carry",
		"goalkicking", "accuracy", "creating", "ruck"]


func run() -> void:
	var args := OS.get_cmdline_user_args().slice(1)
	var starts: Array = args if not args.is_empty() else [Datasets.DEFAULT, "1990"]
	for s in starts:
		GameDB.reload(str(s))
		for p in GameDB.players:
			if bool(p.get("generated", false)) or not p.has("attr"):
				continue
			var vals := []
			for k in KEYS:
				vals.append(str(int((p["attr"] as Dictionary).get(k, 0))))
			print("ATTR %s|%s|%s|%s|%d|%s" % [str(s), str(p.get("club", "")),
					str(p.get("real_name", p.get("name", ""))), str(p.get("role", "")),
					int(p.get("overall", 0)), "|".join(vals)])
	GameDB.reload(Datasets.DEFAULT)
