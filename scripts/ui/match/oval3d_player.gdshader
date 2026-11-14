// PROTOTYPE: the 3D footballer's kit. The pipeline packs the same smooth region fields the
// sprite masks use (kit_<region>): COLOR = guernsey, shorts, sock, boot; UV2.x = hair. Each
// region draws where its field passes 0.5, per pixel, so a hem or armhole is a clean curve.
shader_type spatial;

uniform vec4 skin : source_color = vec4(0.76, 0.57, 0.45, 1.0);
uniform vec4 hair : source_color = vec4(0.15, 0.10, 0.07, 1.0);
uniform vec4 guernsey : source_color;
uniform vec4 shorts : source_color;
uniform vec4 sock : source_color;
uniform vec4 boot : source_color = vec4(0.06, 0.06, 0.07, 1.0);

float edge(float f) {
	float aa = max(fwidth(f), 1e-3);
	return smoothstep(0.5 - aa, 0.5 + aa, f);
}

void fragment() {
	vec3 c = skin.rgb;
	c = mix(c, hair.rgb, edge(UV2.x));
	c = mix(c, boot.rgb, edge(COLOR.a));
	c = mix(c, sock.rgb, edge(COLOR.b));
	c = mix(c, shorts.rgb, edge(COLOR.g));
	c = mix(c, guernsey.rgb, edge(COLOR.r));
	ALBEDO = c;
	ROUGHNESS = 0.82;
}
