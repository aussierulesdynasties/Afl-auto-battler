class_name GroundPacks
extends Node
## A ground's model in its own pack, for a build that leaves the ground models out
## (docs/ITCH_BUILDS.md, "What each build carries"). The build carries res://ground_packs.json,
## written by tools/ground_packs/export.sh: per ground the pack's file, its size and its
## sha256, and "url", the folder the packs are fetched from ("" on the Web: the folder
## "grounds/" beside the page). A pack fetched once is kept in user://grounds/ and loaded from
## there next time; a pack the build no longer lists is deleted.
##
## A source checkout or a build with the models in it lists no packs: ready() is true at
## once for every ground. Use:
##   if not GroundPacks.ready(slug):
##       var packs := GroundPacks.new(); add_child(packs)
##       packs.progress.connect(...); packs.finished.connect(...)   # finished(slug, ok, why)
##       packs.fetch(slug)

## bytes so far, bytes in all
signal progress(slug: String, done: int, total: int)
## ok: the ground's model is in the game now; why: what went wrong, in words for the screen
signal finished(slug: String, ok: bool, why: String)

const MANIFEST := "res://ground_packs.json"
const DIR := "user://grounds/"
## The Web keeps its packs in the browser's storage, which the page holds in memory as it starts:
## at most this many bytes of packs stay there (the newest kept), so a career that has been to
## every ground does not start with them all in memory.
const WEB_KEEP_BYTES := 160 * 1000 * 1000

static var _manifest = null
static var _loaded := {}

var _http: HTTPRequest
var _slug := ""
var _part := ""


## The build's list of packs ({} when the build carries the models itself).
static func manifest() -> Dictionary:
	if _manifest == null:
		_manifest = {}
		if FileAccess.file_exists(MANIFEST):
			var parsed = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
			if parsed is Dictionary:
				_manifest = parsed
	return _manifest


static func entry(slug: String) -> Dictionary:
	var packs = manifest().get("packs", {})
	return packs.get(slug, {}) if packs is Dictionary else {}


## The ground's model is in the game now: in the build itself, or its pack is loaded, or its
## pack is on this device and loads now.
static func ready(slug: String) -> bool:
	if slug == "" or _loaded.has(slug):
		return true
	if not GroundModels.files(slug).is_empty():
		return true
	var e := entry(slug)
	if e.is_empty():
		return false
	var path := DIR + str(e["file"])
	if FileAccess.file_exists(path) and _load(slug, path):
		return true
	return false


## The ground's pack, in MB, for "Download the MCG (27 MB)"; 0 when there is none to fetch.
static func size_mb(slug: String) -> int:
	var e := entry(slug)
	return int(ceil(float(e.get("bytes", 0)) / 1e6)) if not e.is_empty() else 0


## Every ground whose pack this build lists and this device does not have yet.
static func missing() -> PackedStringArray:
	var out := PackedStringArray()
	var packs = manifest().get("packs", {})
	if packs is Dictionary:
		for slug: String in packs:
			if not FileAccess.file_exists(DIR + str(packs[slug]["file"])):
				out.append(slug)
	return out


static func _load(slug: String, path: String) -> bool:
	# replace_files false: a pack only ever adds its ground; it never stands over the build's files.
	if not ProjectSettings.load_resource_pack(path, false):
		push_error("GroundPacks: cannot load %s" % path)
		return false
	if GroundModels.files(slug).is_empty():
		push_error("GroundPacks: %s holds no model for %s" % [path, slug])
		return false
	_loaded[slug] = path.get_file()
	_register_uids(slug)
	return true


## The build's own list of resource ids was made without the ground in it; the pack's imports
## carry each file's id, so the model finds its textures by id as it does in a full build.
static func _register_uids(slug: String) -> void:
	var dir := GroundModels.DIR + slug + "/"
	for f in DirAccess.get_files_at(dir):
		if not f.ends_with(".import"):
			continue
		var cfg := ConfigFile.new()
		if cfg.load(dir + f) != OK:
			continue
		var uid := ResourceUID.text_to_id(str(cfg.get_value("remap", "uid", "")))
		if uid != ResourceUID.INVALID_ID and not ResourceUID.has_id(uid):
			ResourceUID.add_id(uid, dir + f.trim_suffix(".import"))


## Packs the build no longer lists go; on the Web, the oldest fetched go past WEB_KEEP_BYTES.
## A pack loaded this session always stays: the game reads its files from it.
static func tidy(keep := "") -> void:
	var listed := {}
	var packs = manifest().get("packs", {})
	if packs is Dictionary:
		for slug: String in packs:
			listed[str(packs[slug]["file"])] = true
	var da := DirAccess.open(DIR)
	if da == null:
		return
	var in_use := {keep: true}
	for slug: String in _loaded:
		in_use[_loaded[slug]] = true
	var kept: Array = []
	for f in da.get_files():
		if in_use.has(f):
			continue
		if not listed.has(f):
			DirAccess.remove_absolute(DIR + f)
		elif f.ends_with(".pck"):
			kept.append([FileAccess.get_modified_time(DIR + f), f, FileAccess.get_size(DIR + f)])
	if not OS.has_feature("web"):
		return
	kept.sort_custom(func(a, b): return a[0] > b[0])
	var total := 0
	for k in kept:
		total += int(k[2])
		if total > WEB_KEEP_BYTES:
			DirAccess.remove_absolute(DIR + str(k[1]))


## Where the packs are fetched from.
static func base_url() -> String:
	var url := str(manifest().get("url", ""))
	if url != "":
		return url.trim_suffix("/") + "/"
	if OS.has_feature("web"):
		var page = JavaScriptBridge.eval("new URL('grounds/', window.location.href).href", true)
		return str(page)
	return ""


## Fetch the ground's pack and load it; finished() says how it went.
func fetch(slug: String) -> void:
	_slug = slug
	if ready(slug):
		finished.emit.call_deferred(slug, true, "")
		return
	var e := entry(slug)
	var base := base_url()
	if e.is_empty() or base == "":
		finished.emit.call_deferred(slug, false, "This build has no download for this ground.")
		return
	DirAccess.make_dir_recursive_absolute(DIR)
	tidy()
	_part = DIR + str(e["file"]) + ".part"
	_http = HTTPRequest.new()
	# The Web's HTTPRequest hands the body over in memory (it writes no download_file there).
	_http.download_file = "" if OS.has_feature("web") else _part
	_http.use_threads = not OS.has_feature("web")
	_http.timeout = 120.0
	add_child(_http)
	_http.request_completed.connect(_done)
	var err := _http.request(base + str(e["file"]))
	if err != OK:
		_fail("The download could not start (%s)." % error_string(err))


func cancel() -> void:
	if _http != null:
		_http.cancel_request()
		_http.queue_free()
		_http = null
	if _part != "":
		DirAccess.remove_absolute(_part)


func _process(_dt: float) -> void:
	if _http != null:
		var total := int(entry(_slug).get("bytes", _http.get_body_size()))
		progress.emit(_slug, _http.get_downloaded_bytes(), total)


func _done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_http.queue_free()
	_http = null
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		_fail("The download stopped (%s)." % ("no connection" if result != HTTPRequest.RESULT_SUCCESS else "the server said %d" % code))
		return
	if not body.is_empty():
		var f := FileAccess.open(_part, FileAccess.WRITE)
		if f == null:
			_fail("There was no room to keep the download.")
			return
		f.store_buffer(body)
		f.close()
	var e := entry(_slug)
	if FileAccess.get_size(_part) != int(e["bytes"]) or FileAccess.get_sha256(_part) != str(e["sha256"]):
		_fail("The download came in damaged.")
		return
	var path := DIR + str(e["file"])
	DirAccess.rename_absolute(_part, path)
	_part = ""
	if not _load(_slug, path):
		DirAccess.remove_absolute(path)
		finished.emit(_slug, false, "The ground's file would not load.")
		return
	tidy(str(e["file"]))
	finished.emit(_slug, true, "")


func _fail(why: String) -> void:
	if _part != "":
		DirAccess.remove_absolute(_part)
		_part = ""
	finished.emit(_slug, false, why)
