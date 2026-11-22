# Seeded refinement: slide each hand-placed sail up to 5 m onto the darkest spot, penalising overlap with sails already placed.
import json, numpy as np
from PIL import Image
g=255-np.asarray(Image.open('data/riverway/sat.png').convert('L')).astype(float)
F=json.load(open('data/riverway/prep/sails_manual.json'))
def dark(c,a,b,w,h):
    u,v=np.meshgrid(np.linspace(-w/2,w/2,18),np.linspace(-h/2,h/2,12)); P=c+np.outer(u.ravel(),a)+np.outer(v.ravel(),b)
    return g[((1600-P[:,1])*2).astype(int),((P[:,0]+1600)*2).astype(int)].mean()
for f in F:
    th=np.radians(f['angle']); a=np.array([np.cos(th),np.sin(th)]); b=np.array([-a[1],a[0]]); placed=[]
    for i,s in enumerate(f['sails']):
        c0=np.array(s[:2],float); best=None
        for du in np.arange(-5,5.1,.5):
            for dv in np.arange(-5,5.1,.5):
                c=c0+a*du+b*dv; sc=dark(c,a,b,f['w'],f['h'])
                for q in placed:
                    d=c-q; sc-=3*max(0,f['w']-abs(d@a))*max(0,f['h']-abs(d@b))
                if best is None or sc>best[0]: best=(sc,c)
        placed.append(best[1]); f['sails'][i]=[round(float(best[1][0]),1),round(float(best[1][1]),1)]
json.dump(F,open('data/riverway/prep/sails_manual.json','w'))
