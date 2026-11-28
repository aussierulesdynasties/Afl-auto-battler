extends "res://tests/test_match_visual.gd"
## Scratch (never commit): prints every check.


func _check(condition: bool, message: String) -> void:
	print("CHK %s | %s" % ["ok" if condition else "FAIL", message])
	super(condition, message)
