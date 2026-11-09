extends SceneTree
## godot --headless --path . --script tools/audit/run_audit.gd -- <impl>
func _initialize() -> void:
	# The global RNG, seeded: GameState.reset() rolls the career seed from it,
	# so without this two runs of the same audit start different careers.
	# AUDIT_SEED changes it on purpose.
	var env := OS.get_environment("AUDIT_SEED")
	seed(int(env) if env != "" else 2026)
	_run.call_deferred()

func _run() -> void:
	await process_frame
	var path := "res://tools/audit/%s.gd" % OS.get_cmdline_user_args()[0]
	# A script that fails to parse must end the run: Godot would idle forever.
	var script = load(path)
	if script == null or not script.can_instantiate():
		push_error("Audit script did not load: %s" % path)
		quit(1)
		return
	var s = script.new()
	s.run()
	quit(0)
