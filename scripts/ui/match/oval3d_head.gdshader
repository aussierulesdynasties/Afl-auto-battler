// A real player's Tripo head on the body's neck socket (Oval3D.socket_head; row 202, 2d). His own
// texture, and over his neck's bottom 2 cm it blends to the body's skin, so the two meet in one colour:
// by the vertex colour's green where fit_head.py wrote it (skin over the band's bottom 70%), else its red.
shader_type spatial;
// Both sides drawn: where his neck's jagged bottom edge (Gawn's beard) is pulled onto the socket, a few
// small triangles fold over and face inward; drawn, they show skin there instead of a slit.
render_mode cull_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform float rough = 0.6;
instance uniform vec4 skin : source_color = vec4(0.76, 0.57, 0.45, 1.0);

varying float band;

void vertex() {
	band = max(COLOR.r, COLOR.g);
}

void fragment() {
	ALBEDO = mix(texture(tex, UV).rgb, skin.rgb, band);
	ROUGHNESS = rough;
	// A folded triangle seen from behind is lit as if facing out, so it shades like the skin around it.
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
}
