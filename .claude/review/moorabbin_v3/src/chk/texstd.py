# grey stddev (0-255) of every image a material in the built model actually uses (tinted copies included)
import bpy,numpy as np,json
used={}
for m in bpy.data.materials:
    if not m.node_tree:continue
    for n in m.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image:used.setdefault(n.image.name,[]).append(m.name)
R=[]
for k,ms in sorted(used.items()):
    im=bpy.data.images[k];w,h=im.size;a=np.array(im.pixels[:]).reshape(h,w,4)
    al=a[...,3]>0.5
    g=(0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2])[al]*255
    R.append((k,round(float(g.std()),1),round(float(g.mean()),1),sorted(set(ms))))
for r in R:print('STD',r)
json.dump(R,open(bpy.path.abspath('//chk/texstd.json'),'w'),indent=0)
