// The far rows of a ground's seats (GroundModels._seat_far_mesh): one quad a seat, back top to tread
// front, painted as the shell looks from the field, its mipmaps averaging the gaps and rows away.
// Lit as the shell it stands for: the shell's back (leaning 12 degrees) and pan (flat) each take the
// sun by their own normal; the sky comes in by the mesh normal, the two faces' mix. Each seat takes over
// from its shell (seat_near.gdshader) as a whole, at the distance the same hash of the seat picks.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic;
uniform float fade_from = 40.0;
uniform float fade_to = 70.0;

varying vec3 nb;
varying vec3 np;

void vertex() {
	nb = normalize((MODELVIEW_MATRIX * vec4(0.0, 0.2085, 0.978, 0.0)).xyz);
	np = normalize((MODELVIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	float d = length((MODELVIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz);
	float h = fract(sin(float(INSTANCE_ID) * 12.9898 + 78.233) * 43758.5453);
	if ((d - fade_from) / (fade_to - fade_from) <= h) {
		VERTEX = vec3(0.0);   // still drawn by its shell
	}
}

void fragment() {
	ALBEDO = texture(tex, UV).rgb;
	ROUGHNESS = 1.0;
	AO = 0.85;
	AO_LIGHT_AFFECT = 0.0;
}

void light() {
	// Each face's share of the shell's light, fitted to the shells' own render at Bellerive (2026-11-23,
	// cloud render, both stands within 6 of each channel): the back as seen from the field takes half,
	// the pan a little under a quarter (the rest of the shell is in its own shade).
	float lam = 0.5 * max(dot(nb, LIGHT), 0.0) + 0.22 * max(dot(np, LIGHT), 0.0);
	DIFFUSE_LIGHT += lam * ATTENUATION * LIGHT_COLOR / PI;
}
