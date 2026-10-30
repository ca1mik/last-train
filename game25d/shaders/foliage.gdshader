shader_type spatial;
render_mode cull_disabled;
uniform vec4 leaf_color : source_color = vec4(0.22,0.32,0.19,1.0);
uniform float wind_strength = 0.055;
void vertex() {
 vec3 world = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz;
 float weight = clamp(VERTEX.y + 0.5,0.0,1.0);
 VERTEX.x += sin(TIME*0.9+world.x*0.45+world.z*0.3)*wind_strength*weight;
 VERTEX.z += cos(TIME*0.7+world.z*0.4)*wind_strength*0.45*weight;
}
void fragment() {
 ALBEDO=leaf_color.rgb*COLOR.rgb;
 ROUGHNESS=0.93;
}
