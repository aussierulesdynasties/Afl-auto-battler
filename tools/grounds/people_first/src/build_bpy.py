# Run build.py with the bpy module instead of Blender (no render): python3 build_bpy.py OUT.glb
import sys
out = sys.argv[1]
src = open("build.py").read().split("sc=bpy.context.scene;sc.render.engine")[0]
sys.argv = ["blender", "--", out, "render.png"]
exec(compile(src, "build.py", "exec"))
