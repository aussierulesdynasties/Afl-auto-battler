// The near seat shells of a ground whose seats turn into far rows (GroundModels.SEAT_FAR): lit as
// StandardMaterial3D lights them, flat in one colour. Between fade_from and fade_to each seat as a whole
// gives way to its far quad (seat_far.gdshader) at its own distance, a hash of the seat picking where in the
// band: no pixel dither, which read as fine noise across both tiers on the PC (Bellerive check r5).
shader_type spatial;
render_mode cull_disabled;

uniform vec4 albedo : source_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform float fade_from = 40.0;
uniform float fade_to = 70.0;

void vertex() {
	float d = length((MODELVIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz);
	float h = fract(sin(float(INSTANCE_ID) * 12.9898 + 78.233) * 43758.5453);
	if ((d - fade_from) / (fade_to - fade_from) > h) {
		VERTEX = vec3(0.0);   // this seat is drawn by its far quad: every triangle collapses to a point
	}
}

void fragment() {
	ALBEDO = albedo.rgb;
	ROUGHNESS = 1.0;
}
