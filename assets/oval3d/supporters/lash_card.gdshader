// Close-up supporter eyelashes: each lash is thinner than a pixel at close-up range, so they are drawn
// see-through (a soft dark line, as a camera sees lashes), with the alpha raised per mip level so the
// shrunk picture doesn't fade them away (same idea as hair_card.gdshader).
shader_type spatial;
render_mode cull_disabled, blend_mix, depth_draw_never;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_colour : source_color = vec4(1.0);
uniform vec2 tex_size = vec2(2048.0);
uniform float mip_scale = 0.5;
uniform float roughness = 0.9;
uniform float specular = 0.2;

void fragment() {
	vec4 t = texture(albedo_tex, UV) * albedo_colour;
	vec2 px = UV * tex_size;
	float lod = max(0.0, 0.5 * log2(max(dot(dFdx(px), dFdx(px)), dot(dFdy(px), dFdy(px)))));
	ALBEDO = t.rgb;
	ALPHA = clamp(t.a * (1.0 + lod * mip_scale), 0.0, 1.0);
	ROUGHNESS = roughness;
	SPECULAR = specular;
}
