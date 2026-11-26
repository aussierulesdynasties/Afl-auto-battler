# Blender-module wrapper for drop_field.py (chain.sh): open the blend, then run drop_field with its usual argv
import bpy,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
sys.argv=[sys.argv[0],'--',sys.argv[sys.argv.index('--')+2]]
exec(open('drop_field.py').read())
