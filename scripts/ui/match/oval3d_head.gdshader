// A real player's Tripo head on the body's neck socket (Oval3D.socket_head; row 202, 2d). His own
// texture, and over his neck's bottom 2 cm it blends to the body's skin, so the two meet in one colour:
// by the vertex colour's green where fit_head.py wrote it (skin over the band's bottom 70%), else its red.
// The skin it blends to is the body's own at the ring below (CUSTOM0, Oval3D._ring_skin): his skin colour
// times the MetaHuman map there, and the map's sheen, so the join shows no change of tone or shine.
shader_type spatial;
// Both sides drawn in the band: where his neck's jagged bottom edge (Gawn's beard) is pulled onto the
// socket, a few small triangles fold over and face inward; drawn, they show skin there instead of a slit.
render_mode cull_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform float rough = 0.6;
uniform vec3 beard_dark : source_color = vec3(0.06, 0.04, 0.03);
instance uniform vec4 skin : source_color = vec4(0.76, 0.57, 0.45, 1.0);

varying float band;
varying vec4 ring_skin;

void vertex() {
	band = max(COLOR.r, COLOR.g);
	ring_skin = CUSTOM0;
}

void fragment() {
	ALBEDO = mix(texture(tex, UV).rgb, skin.rgb * ring_skin.rgb, band);
	// Above the band a back is the inside of a beard card: its texture there is skin (a pale shard in his
	// beard), so it takes the beard's own dark instead; it still closes the scan's holes.
	ROUGHNESS = mix(rough, ring_skin.a, band);
	if (!FRONT_FACING && band < 0.5) {
		ALBEDO = beard_dark;
		ROUGHNESS = 1.0;
		SPECULAR = 0.0;
	}
	// A folded triangle seen from behind is lit as if facing out, so it shades like the skin around it.
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}
