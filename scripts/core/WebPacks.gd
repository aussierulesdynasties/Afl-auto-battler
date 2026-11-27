extends Node
## The web build's textures ship in a pack of their own, one per graphics family (PC
## graphics cards draw S3TC/BPTC, phones ETC2/ASTC), and the page downloads only the one
## its browser draws with (tools/web_texture_packs.py, bug bash M-12). This first autoload
## mounts that pack before any other script compiles, so every texture loads exactly as
## it did from the one big pack. Nothing happens off the web, or when the pack is absent.

const PACK := "textures.pck"   # where the page puts it (index.html, Engine.preloadFile)


func _init() -> void:
	if OS.has_feature("web") and FileAccess.file_exists(PACK):
		if not ProjectSettings.load_resource_pack(PACK, false):
			push_error("WebPacks: could not mount %s" % PACK)
