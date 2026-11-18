import json,sys,os,numpy as np
HERE=os.path.dirname(os.path.abspath(sys.argv[0]));__file__=os.path.join(HERE,'sv.py')
exec(open(os.path.join(HERE,'sv.py'),encoding='utf-8').read().split('if __name__')[0])
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
db=json.load(open(os.path.join(HERE,'panos.json')))
G=json.load(open(os.path.join(MV,'osm/geo.json'),encoding='utf-8'));a=np.array(G['ways']['22971441'])
q=loc(np.c_[a,np.zeros(len(a))])[:-1];q=np.r_[q,q[:1]]
fig,ax=plt.subplots(figsize=(11,11),dpi=80);ax.plot(-q[:,1],-q[:,0],'k-',lw=2)
cols={};pal=plt.cm.tab10.colors
for k,v in db.items():
    if 's' not in v:continue
    d=v.get('date','?');c=cols.setdefault(d,pal[len(cols)%10])
    ax.plot(-v['t'],-v['s'],'o',color=c,ms=5 if v.get('done') else 2)
for d,c in cols.items():ax.plot([],[],'o',color=c,label=d)
ax.legend();ax.set_aspect('equal');ax.set_title('Street View panoramas (north up); big = visited');plt.savefig(os.path.join(HERE,'panos_plan.png'))
from collections import Counter;print(len(db),Counter(v.get('date') for v in db.values()))
