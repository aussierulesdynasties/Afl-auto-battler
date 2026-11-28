extends RefCounted
## Scratch (bug bash, never commit): the candidate CareerSave._encode, for a byte-for-byte check.

const PLAYER_REF := "__player_ref"
const WRITE_TAG := "__save_sid"
const SKIP_PLAYER_KEYS := ["rates", "norm"]

var _players := {}
var _next_sid := 0
var _tagged: Array = []


func _encode(v):
	if v is Dictionary:
		var d: Dictionary = v
		if d.has("id") and d.has("attr") and d.has("role"):
			if not d.has(WRITE_TAG):
				var sid := _next_sid
				_next_sid += 1
				d[WRITE_TAG] = sid
				_tagged.append(d)
				_players[sid] = _player_body(d)
			return {PLAYER_REF: int(d[WRITE_TAG])}
		if d.is_typed():
			return _dict_slow(d)
		# The copy is made in the engine; only the containers in it are walked.
		var out := d.duplicate()
		for k in d:
			var x = d[k]
			var t := typeof(x)
			if t == TYPE_DICTIONARY or t == TYPE_ARRAY:
				out[k] = _encode(x)
		return out
	if v is Array:
		var a: Array = v
		if a.is_typed():
			var slow := []
			for x in a:
				var t := typeof(x)
				slow.append(_encode(x) if t == TYPE_DICTIONARY or t == TYPE_ARRAY else x)
			return slow
		var out := a.duplicate()
		for i in range(a.size()):
			var t := typeof(a[i])
			if t == TYPE_DICTIONARY or t == TYPE_ARRAY:
				out[i] = _encode(a[i])
		return out
	return v


func _player_body(d: Dictionary) -> Dictionary:
	if d.is_typed():
		var slow := {}
		for k in d:
			if k != WRITE_TAG and not SKIP_PLAYER_KEYS.has(k):
				var x = d[k]
				var t := typeof(x)
				slow[k] = _encode(x) if t == TYPE_DICTIONARY or t == TYPE_ARRAY else x
		return slow
	var body := d.duplicate()
	body.erase(WRITE_TAG)
	for k in SKIP_PLAYER_KEYS:
		body.erase(k)
	for k in d:
		var x = d[k]
		var t := typeof(x)
		if (t == TYPE_DICTIONARY or t == TYPE_ARRAY) and not SKIP_PLAYER_KEYS.has(k):
			body[k] = _encode(x)
	return body


func _dict_slow(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		var x = d[k]
		var t := typeof(x)
		out[k] = _encode(x) if t == TYPE_DICTIONARY or t == TYPE_ARRAY else x
	return out


func _untag() -> void:
	for d in _tagged:
		(d as Dictionary).erase(WRITE_TAG)
	_tagged = []
