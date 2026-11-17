// Close-up supporter hair, brows and lashes: thin cut-out cards that stay smooth instead of scratchy.
// Mipmaps blur the picture as it shrinks, which smooths the strands but fades thin hairs (lashes) below the
// cut-off, so each mip level raises the cut-out's alpha a little to keep the strands' coverage
// (Ben Golus, "Anti-aliased Alpha Test: The Esoteric Alpha To Coverage", 2017), and MSAA alpha-to-coverage
// softens the edges.
shader_type spatial;
render_mode cull_disabled, alpha_to_coverage_and_one;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo_colour : source_color = vec4(1.0);
uniform vec2 tex_size = vec2(2048.0);
uniform float cutoff = 0.3;
uniform float mip_scale = 0.25;   // alpha gain per mip level (Golus)
uniform float roughness = 0.9;
uniform float specular = 0.2;

void fragment() {
	vec4 t = texture(albedo_tex, UV) * albedo_colour;
	vec2 px = UV * tex_size;
	float lod = max(0.0, 0.5 * log2(max(dot(dFdx(px), dFdx(px)), dot(dFdy(px), dFdy(px)))));
	ALBEDO = t.rgb;
	ALPHA = t.a * (1.0 + lod * mip_scale);
	ALPHA_SCISSOR_THRESHOLD = cutoff;
	ALPHA_ANTIALIASING_EDGE = cutoff;
	ALPHA_TEXTURE_COORDINATE = px;
	ROUGHNESS = roughness;
	SPECULAR = specular;
}
