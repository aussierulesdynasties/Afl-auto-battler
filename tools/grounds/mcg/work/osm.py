import sys,json,numpy as np;sys.path.insert(0,'work');import geo,tri,earthcam as E
from PIL import Image,ImageDraw
D=json.load(open('osm/mcg.json',encoding='utf-8'));N={e['id']:(e['lat'],e['lon']) for e in D['elements'] if e['type']=='node'}
W={e['id']:e for e in D['elements'] if e['type']=='way'}
def xy(nid):return geo.ll2xy(*N[nid])
keep={8037539:'pitch',210337258:'stadium',32000530:'shane_warne',131709272:'mcc',131709273:'olympic',131709274:'ponsford'}
out={k:[list(map(lambda t:round(float(t),2),xy(n))) for n in W[i]['nodes']] for i,k in keep.items()}
out['flagpoles']=[list(map(lambda t:round(float(t),2),geo.ll2xy(e['lat'],e['lon']))) for e in D['elements'] if e['type']=='node' and e.get('tags',{}).get('man_made')=='flagpole']
out['towers']=[list(map(lambda t:round(float(t),2),geo.ll2xy(e['lat'],e['lon']))) for e in D['elements'] if e['type']=='node' and e.get('tags',{}).get('man_made')=='tower']
json.dump(out,open('work/osm_xy.json','w'),indent=0)
c=tri.camv('n_c');im=Image.open('ge/n_c.png').convert('RGB');d=ImageDraw.Draw(im)
col={'pitch':(255,0,255),'stadium':(0,255,255),'shane_warne':(255,128,0),'mcc':(255,255,0),'olympic':(0,255,0),'ponsford':(255,0,0)}
for k,z in [('pitch',-5.3),('stadium',0),('shane_warne',0),('mcc',0),('olympic',0),('ponsford',0)]:
    P=[tuple(E.proj(c,[x,y,z])) for x,y in out[k]];d.line(P,fill=col[k],width=2)
for x,y in out['flagpoles']+out['towers']:
    p=E.proj(c,[x,y,0]);d.ellipse([p[0]-4,p[1]-4,p[0]+4,p[1]+4],outline=(255,255,255),width=2)
im.crop((480,120,1440,960)).save('work/osm_nc.png')
for k in keep.values():
    a=np.array(out[k]);print(k,len(a),'x',a[:,0].min().round(1),a[:,0].max().round(1),'y',a[:,1].min().round(1),a[:,1].max().round(1))
print('towers',out['towers'])
