import bpy, sys
for mn,col in (('seats_up',(214,117,104)),('seats',(216,105,91))):
    m=bpy.data.materials[mn]; nt=m.node_tree
    b=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'][0]
    for l in list(b.inputs['Base Color'].links): nt.links.remove(l)
    b.inputs['Base Color'].default_value=[ (c/255)**2.2 for c in col]+[1]
exec(open('render.py').read())
