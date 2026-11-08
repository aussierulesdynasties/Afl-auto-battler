extends RefCounted
func run() -> void:
	var out := []
	var code := OS.execute(OS.get_executable_path(), ["--headless", "--path", ".", "--script", "res://tests/run_stats_tests.gd"], out, true)
	print("STATS exit ", code)
	for chunk in out:
		for l in str(chunk).split("\n"):
			if l.contains("FAIL") or l.contains("PROBE") or l.contains("ERROR: The") or l.contains("checks") or l.contains("Wrote"):
				print(l)
	var f := FileAccess.get_file_as_string("res://tests/fixtures/awards_round4_snapshot.txt")
	for l in f.split("\n"):
		print("SNAP|", l)
