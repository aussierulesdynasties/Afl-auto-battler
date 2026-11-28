extends "res://tests/test_match_game.gd"
## Scratch (never commit): prints every check of one test function.


func _check(condition: bool, message: String) -> void:
	print("CHK %s | %s" % ["ok" if condition else "FAIL", message])
	super(condition, message)
