// The land round a ground with a near map (GroundModels.SURROUNDS "near_map"): the 1 m map over the whole ring and,
// within near_span m of the middle, the near map at its finer scale (Bellerive: 768 m at 0.375 m), blending into the
// 1 m map over the near map's last 4 %. Lit as the plain ring's StandardMaterial3D: rough, no specular, no shadows received.
shader_type spatial;
render_mode shadows_disabled;

uniform sampler2D far_map : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D near_map : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float span = 2048.0;
uniform float near_span = 768.0;

varying vec2 xz;

void vertex() {
	xz = VERTEX.xz;
}

void fragment() {
	vec3 c = texture(far_map, xz / span + 0.5).rgb;
	vec2 un = xz / near_span + 0.5;
	float edge = max(abs(un.x - 0.5), abs(un.y - 0.5));
	float w = 1.0 - smoothstep(0.46, 0.5, edge);
	if (w > 0.0) {
		c = mix(c, texture(near_map, un).rgb, w);
	}
	ALBEDO = c;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
