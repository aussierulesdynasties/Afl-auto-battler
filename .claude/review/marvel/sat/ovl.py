import sys,os,json,numpy as np
HERE=os.path.dirname(os.path.abspath(sys.argv[0]));SV=os.path.join(HERE,'..','sv');__file__=os.path.join(SV,'sv.py')
exec(open(os.path.join(SV,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
from PIL import Image,ImageDraw
im=Image.open('lplan_all.jpg');dr=ImageDraw.Draw(im);s0,t1,M=-200,200,0.25
P=lambda s,t:((t1-t)/M,(s-s0)/M)
G=json.load(open(os.path.join(MV,'osm/geo.json')))
for wid,col in (('22971441','red'),('751006317','orange'),('1043590391','lime')):
    a=np.array(G['ways'][wid]);q=loc(np.c_[a,np.zeros(len(a))]);dr.line([P(*p) for p in q],fill=col,width=2)
pj=json.load(open(os.path.join(MV,'parts.json')))['parts']
for p in pj:
    if p['name'] in('roof_ring','tower_NW','tower_SW','tower_T1','tower_T2','deck','plaza','pavilion'):
        V=np.array(p['V']);q=loc(V);n=len(q)//2 if p['name']!='roof_ring' else len(q)//2
        dr.line([P(*x) for x in q[:n]]+[P(*q[0])],fill='magenta',width=2)
im.save('ovl.jpg',quality=90)
