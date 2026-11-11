class_name GameLogo
## The game's logo. This is the one place its file is named: the title screen
## (Main) and the load screens (LoadFlair) both read it from here.
##
## PLACEHOLDER ART (TODO row V9). The file below is a stand-in until the
## director supplies the final logo. To replace it: add the new file, point
## TEXTURE at it, set REGION to its lettering, and set PLACEHOLDER to false.
## Nothing else in the game needs to change.

## True while the logo is the stand-in, false once the final art is in.
const PLACEHOLDER := true
const TEXTURE := preload("res://assets/ui/aussie_rules_dynasties_logo_placeholder.png")
## The lettering's part of the file (1536 x 1024, mostly black ground), with
## a little room, so whatever sits under the logo sits under the words rather
## than the ground.
const REGION := Rect2(90, 228, 1374, 614)


## The lettering alone, ready to put on a TextureRect.
static func art() -> AtlasTexture:
	var tex := AtlasTexture.new()
	tex.atlas = TEXTURE
	tex.region = REGION
	return tex


## Height over width of the lettering.
static func aspect() -> float:
	return REGION.size.y / REGION.size.x
