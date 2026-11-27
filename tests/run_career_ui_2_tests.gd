extends "res://tests/run_career_ui_tests.gd"
## godot --headless --path . --script tests/run_career_ui_2_tests.gd
## The second half of the career UI suite: the PART_TWO functions of
## tests/run_career_ui_tests.gd (event cards, the sacked coach's and rival
## board's offers, skipping ahead, the list screen), after the same setup.
## Seeded by design: it inherits SUITE_SEED and the replay_seed setup from that runner.


func _part_two() -> bool:
	return true
