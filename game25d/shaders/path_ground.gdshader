shader_type spatial;
render_mode cull_disabled;
uniform vec4 ground_color : source_color = vec4(0.38,0.37,0.27,1.0);
varying vec3 world_position;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;}
void fragment(){
 float grain=hash(floor(world_position.xz*18.0));
 float rough_edge=hash(floor(world_position.xz*2.2));
 float edge=smoothstep(0.0,0.2,UV.x)*smoothstep(0.0,0.2,1.0-UV.x);
 float end=smoothstep(0.0,0.06,UV.y)*smoothstep(0.0,0.06,1.0-UV.y);
 ALBEDO=ground_color.rgb*(0.86+grain*0.21);
 ROUGHNESS=0.98;ALPHA=edge*end*(0.65+rough_edge*0.30);
}
