// A ground's far land (GroundModels.backdrop, a mesh named terrain_shaded): its colour and its hill shade
// are in its vertex colours (sRGB), drawn unshaded so the sky's blue fill does not turn the bush navy.
// Near the ground a painted map of the plain (`plain`, `span` m a side, north up, centred on the
// model's origin) is laid over it, faded by its own alpha and by the vertex alpha (0 on the sea).
// Looks only.
shader_type spatial;
render_mode unshaded, shadows_disabled;

uniform sampler2D plain : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float span = 10240.0;
uniform bool has_plain = false;
varying vec2 map_uv;

void vertex() {
	map_uv = VERTEX.xz / span + 0.5;
}

void fragment() {
	vec3 c = pow(COLOR.rgb, vec3(2.2));
	if (has_plain && map_uv.x > 0.0 && map_uv.x < 1.0 && map_uv.y > 0.0 && map_uv.y < 1.0) {
		vec4 p = texture(plain, map_uv);
		c = mix(c, p.rgb, p.a * COLOR.a);
	}
	ALBEDO = c;
}
