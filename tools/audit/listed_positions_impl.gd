extends RefCounted
## Every 2026 real player's listed position (real_pos) against the first
## position and OVR the game gives him (TODO row 91, T8.Q11). One parseable
## line per player:
##   ROW id|club|name|listed|role|role2|overall|potential|gm
## then a summary: listed x first position, and the median OVR of each first
## position. Run it on two checkouts and join on id to list every move.
## Reads; changes nothing. No arguments.


func run() -> void:
	var cross := {}
	var by_role := {}
	for p in GameDB.players:
		var listed := str(p.get("real_pos", ""))
		var role := str(p.get("role", ""))
		print("ROW %s|%s|%s|%s|%s|%s|%d|%d|%d" % [str(p.get("id", "")), str(p.get("club", "")),
				str(p.get("real_name", "")), listed, role, str(p.get("role2", "")),
				int(p.get("overall", 0)), int(p.get("potential", 0)), int(p.get("gm", 0))])
		var k := "%s>%s" % [listed if listed != "" else "(none)", role]
		cross[k] = int(cross.get(k, 0)) + 1
		if not by_role.has(role):
			by_role[role] = []
		(by_role[role] as Array).append(int(p.get("overall", 0)))
	print("PLAYERS %d" % GameDB.players.size())
	var keys := cross.keys()
	keys.sort()
	for k in keys:
		print("CROSS %s %d" % [k, int(cross[k])])
	for r in ["FWD", "MID", "DEF", "RUCK"]:
		var v: Array = by_role.get(r, [])
		v.sort()
		print("MEDIAN %s n=%d ovr=%d" % [r, v.size(), int(v[v.size() / 2]) if not v.is_empty() else 0])
