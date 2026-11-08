extends RefCounted
func run() -> void:
	var out := []
	OS.set_environment("GODOT", OS.get_executable_path())
	OS.set_environment("JOBS", "1")
	OS.set_environment("SUITES_ONLY", "1")
	OS.set_environment("SKIP_VERSION_CHECK", "1")
	var code := OS.execute("bash", ["-c", "tools/run_tests.sh stats; d=$(ls -dt /tmp/*/ | head -5); for x in $d; do if [ -f $x/stats.log ]; then echo LOGDIR $x; grep -E 'PROBE|ERROR: |Wrote|checks' $x/stats.log | cut -c1-220; fi; done"], out, true)
	print("STATS exit ", code)
	for chunk in out:
		for l in str(chunk).split("\n"):
			print(l)
	var f := FileAccess.get_file_as_string("res://tests/fixtures/awards_round4_snapshot.txt")
	for l in f.split("\n"):
		print("SNAP|", l)
