class_name SaveFiles
extends RefCounted
## Moving a career backup between the game and the coach's own files (row 57).
## The web build downloads the file and reads one through the browser's file
## picker; desktop and Android use the system's file dialog. Only the bytes
## cross: GameState decides what they mean.

const FILTER := "*.ardsave ; Career backup"
## The browser picker's answer: base64 bytes, "cancel", or "" while open.
const WEB_KEY := "__aflImport"


## Offer `bytes` as a file called `file_name`. `done` gets true once written
## (on the web, once the download is handed to the browser).
static func save_to_device(host: Control, bytes: PackedByteArray, file_name: String, done: Callable) -> void:
	if OS.has_feature("web"):
		JavaScriptBridge.download_buffer(bytes, file_name, "application/octet-stream")
		done.call(true)
		return
	var dlg := _dialog(host, FileDialog.FILE_MODE_SAVE_FILE)
	dlg.current_file = file_name
	dlg.file_selected.connect(func(path: String):
		var f := FileAccess.open(path, FileAccess.WRITE)
		var ok := f != null
		if ok:
			f.store_buffer(bytes)
			f.close()
		dlg.queue_free()
		done.call(ok))
	dlg.canceled.connect(func(): dlg.queue_free())
	dlg.popup_centered_ratio(0.8)


## Let the coach pick a backup file; `got` receives its bytes (never called
## on cancel).
static func pick_from_device(host: Control, got: Callable) -> void:
	if OS.has_feature("web"):
		_web_pick(host, got)
		return
	var dlg := _dialog(host, FileDialog.FILE_MODE_OPEN_FILE)
	dlg.file_selected.connect(func(path: String):
		dlg.queue_free()
		got.call(FileAccess.get_file_as_bytes(path)))
	dlg.canceled.connect(func(): dlg.queue_free())
	dlg.popup_centered_ratio(0.8)


static func _dialog(host: Control, mode: FileDialog.FileMode) -> FileDialog:
	var dlg := FileDialog.new()
	dlg.file_mode = mode
	dlg.access = FileDialog.ACCESS_FILESYSTEM
	dlg.use_native_dialog = true
	dlg.filters = PackedStringArray([FILTER])
	host.add_child(dlg)
	return dlg


## The browser's file input, opened from the button press (it still counts
## as the coach's tap); the file comes back as base64 through a window key.
static func _web_pick(host: Control, got: Callable) -> void:
	JavaScriptBridge.eval(
			"window." + WEB_KEY + "='';(function(){var i=document.createElement('input');"
			+ "i.type='file';i.accept='.ardsave';"
			+ "i.addEventListener('cancel',function(){window." + WEB_KEY + "='cancel';});"
			+ "i.onchange=function(){var f=i.files&&i.files[0];if(!f){window." + WEB_KEY + "='cancel';return;}"
			+ "var r=new FileReader();r.onload=function(){var b=new Uint8Array(r.result),s='';"
			+ "for(var k=0;k<b.length;k+=32768){s+=String.fromCharCode.apply(null,b.subarray(k,k+32768));}"
			+ "window." + WEB_KEY + "=btoa(s)||'cancel';};"
			+ "r.onerror=function(){window." + WEB_KEY + "='cancel';};r.readAsArrayBuffer(f);};"
			+ "i.click();})();", true)
	# A picker can stay open a long while; give up after ten minutes.
	for n in range(1200):
		await host.get_tree().create_timer(0.5).timeout
		if not is_instance_valid(host):
			return
		var v := str(JavaScriptBridge.eval("window." + WEB_KEY + "||''", true))
		if v == "":
			continue
		JavaScriptBridge.eval("window." + WEB_KEY + "=''", true)
		if v != "cancel":
			got.call(Marshalls.base64_to_raw(v))
		return
