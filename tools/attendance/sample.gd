extends SceneTree
## A sample of the crowds MatchAttendance draws, to check them against real AFL figures:
##   godot --headless --path . --script tools/attendance/sample.gd
## Prints each fixture's crowd and the share of its ground it fills. Looks only.

const CASES := [
	["MCG", "COL", "ESS", "day", "Round 7"], ["MCG", "COL", "CAR", "night", "Round 1"],
	["MCG", "MEL", "GCS", "day", "Round 14"], ["MCG", "RIC", "CAR", "night", "Round 0"],
	["MCG", "HAW", "GEE", "day", "Qualifying Final 1"], ["MCG", "COL", "BRL", "day", "Grand Final"],
	["Marvel Stadium", "NTH", "GWS", "day", "Round 9"], ["Marvel Stadium", "ESS", "CAR", "night", "Round 5"],
	["Adelaide Oval", "ADE", "PAD", "night", "Round 8"], ["Adelaide Oval", "PAD", "GWS", "day", "Round 18"],
	["Optus Stadium", "WCE", "FRE", "day", "Round 11"], ["Optus Stadium", "FRE", "STK", "twilight", "Round 3"],
	["SCG", "SYD", "COL", "night", "Round 4"], ["The Gabba", "BRL", "NTH", "night", "Round 16"],
	["Engie Stadium", "GWS", "WBD", "day", "Round 20"], ["People First Stadium", "GCS", "RIC", "day", "Round 6"],
	["GMHBA Stadium", "GEE", "WCE", "day", "Round 10"], ["Bellerive Oval", "NTH", "ADE", "day", "Round 13"],
	["Waverley Park", "HAW", "STK", "day", "Round 3"], ["Accor Stadium", "SYD", "GWS", "night", "Round 2"],
]


func _initialize() -> void:
	for c in CASES:
		var crowds := []
		for k in range(200):
			crowds.append(MatchAttendance.crowd(c[0], c[1], c[2], c[3], c[4], k))
		crowds.sort()
		var one := MatchAttendance.crowd(c[0], c[1], c[2], c[3], c[4], 7)
		print("%-22s %s v %s %-8s %-20s typical %6d (%d-%d)  fills %.0f%%" % [c[0], c[1], c[2], c[3], c[4],
				crowds[100], crowds[10], crowds[190], 100.0 * MatchAttendance.fill(c[0], one)])
	quit()
