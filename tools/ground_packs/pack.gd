extends SceneTree
## Packs a folder of res:// files (strip.py's output) into one Godot pack.
##   godot --headless --script tools/ground_packs/pack.gd -- <dir> <out.pck>

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var dir: String = args[0]
	var packer := PCKPacker.new()
	var err := packer.pck_start(args[1])
	if err == OK:
		err = _add(packer, dir, "")
	if err == OK:
		err = packer.flush()
	if err != OK:
		push_error("pack.gd: %s" % error_string(err))
	quit(0 if err == OK else 1)


func _add(packer: PCKPacker, dir: String, rel: String) -> Error:
	var da := DirAccess.open(dir.path_join(rel))
	if da == null:
		return ERR_CANT_OPEN
	da.include_hidden = true
	for f in da.get_files():
		var err := packer.add_file("res://" + rel.path_join(f).trim_prefix("/"), dir.path_join(rel).path_join(f))
		if err != OK:
			return err
	for d in da.get_directories():
		var err := _add(packer, dir, rel.path_join(d))
		if err != OK:
			return err
	return OK
