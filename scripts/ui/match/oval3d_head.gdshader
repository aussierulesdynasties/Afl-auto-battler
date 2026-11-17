// A real player's Tripo head on the body's neck socket (Oval3D.socket_head; row 202, 2d). His own
// texture, and over his neck's bottom 2 cm (the vertex colour's red: 1 on the socket, 0 from 2 cm up)
// it blends to the body's skin, so the two meet in one colour.
shader_type spatial;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform float rough = 0.6;
instance uniform vec4 skin : source_color = vec4(0.76, 0.57, 0.45, 1.0);

varying float band;

void vertex() {
	band = COLOR.r;
}

void fragment() {
	ALBEDO = mix(texture(tex, UV).rgb, skin.rgb, band);
	ROUGHNESS = rough;
}
