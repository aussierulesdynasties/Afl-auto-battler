import bpy,json,math
T=json.load(open(r'D:/Temp/claude/2117a0e07442304a/b457f311-065b-4525-9ffd-7c62765dd586/scratchpad/obuild/truss.json'))
V=[]
for o in bpy.data.objects:
    if o.type=='MESH':V+= [o.matrix_world@v.co for v in o.data.vertices]
import mathutils
kd=mathutils.kdtree.KDTree(len(V))
for i,v in enumerate(V):kd.insert(mathutils.Vector((v.x,v.y,0)),i)
kd.balance()
e=[kd.find(mathutils.Vector((t['o'][0],t['o'][1],0)))[2] for t in T]
f=[kd.find(mathutils.Vector((t['i'][0],t['i'][1],0)))[2] for t in T]
print('RES outer nearest vert mean %.2f max %.2f; inner mean %.2f max %.2f'%(sum(e)/50,max(e),sum(f)/50,max(f)))
