extends SceneTree
## Compile-checks test runners without running them (tools/ci_preflight_compile.sh).
##   godot --headless --path . --script tools/ci_preflight_compile.gd -- res://tests/run_a_tests.gd ...
## Loads each script by path inside _initialize(), which runs AFTER the autoload
## names exist, so it catches parse errors and hanging loads but not a runner that
## names an autoload-dependent class at compile time; ci_preflight_compile.sh's
## second pass (--check-only --script per runner) catches that. Prints "LOADING <path>" first, so if a load hangs the
## caller knows which one; then "OK <path>" or "FAIL <path>". Exits 1 on the first failure.


func _initialize() -> void:
	var paths := OS.get_cmdline_user_args()
	if paths.is_empty():
		print("FAIL no script paths given")
		quit(1)
		return
	for path in paths:
		print("LOADING ", path)
		var script = load(path)
		if script == null or not script is GDScript or not script.can_instantiate():
			print("FAIL ", path)
			quit(1)
			return
		print("OK ", path)
	quit(0)
