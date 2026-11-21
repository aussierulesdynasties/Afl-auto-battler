import sys,json,numpy as np;sys.path.insert(0,'.')
from frame import *
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from PIL import Image
G=json.load(open('osm/geo.json'));a=np.array(G['ways']['22971441']);q=loc(np.c_[a,np.zeros(len(a))])[:-1]
cov={};cam=loc(np.array([[-272.107,-104.797,0]]))[0][:2];ctr=q[:,:2].mean(0)
for i in range(len(q)):
    p,n=q[i][:2],q[(i+1)%len(q)][:2];m=(p+n)/2;d=n-p;nm=np.array([d[1],-d[0]]);nm/=np.linalg.norm(nm)
    if nm@(m-ctr)<0:nm=-nm
    tc=(cam-m)/np.linalg.norm(cam-m)
    if m[0]>95 or i in (9,10):cov[i]=('2024 photos: glass south end, Gates 1-3 (Bourke St)','#1565c0')
    elif 48<=i<=50:cov[i]=('2024 photos: City Edge, Gate 5 (east)','#6a1b9a')
    elif nm@tc>0.3:cov[i]=('2019 aerial: west side, unchanged since 2019','#2e7d32')
    else:cov[i]=('NO PHOTO FOUND: north end (La Trobe St) and north-east side','#d32f2f')
fig=plt.figure(figsize=(16,20),dpi=80)
ax=fig.add_axes([0.03,0.52,0.45,0.45]);seen=set()
for i in range(len(q)):
    l,c=cov[i];p,n=q[i],q[(i+1)%len(q)]
    ax.plot([-p[1],-n[1]],[-p[0],-n[0]],color=c,lw=9,solid_capstyle='butt',label=None if l in seen else l);seen.add(l)
ax.set_aspect('equal');ax.axis('off');ax.legend(loc='lower center',bbox_to_anchor=(0.5,-0.22),fontsize=13)
for txt,xy in (('NORTH\nLa Trobe St',(0,150)),('SOUTH\nBourke St',(0,-150)),('WEST\nHarbour Esplanade',(-160,0)),('EAST\nWurundjeri Way',(160,0))):
    ax.text(*xy,txt,ha='center',va='center',fontsize=13,weight='bold')
ax.set_xlim(-200,200);ax.set_ylim(-190,190);ax.set_title('Which photo covers each side (plan, north up)',fontsize=16,weight='bold')
ax2=fig.add_axes([0.5,0.52,0.48,0.45]);ax2.axis('off')
ax2.text(0,0.95,'Sources searched for the north and east sides:',fontsize=14,weight='bold',transform=ax2.transAxes)
ax2.text(0,0.88,'Wikimedia Commons: every Marvel/Docklands file\nPexels: 8 photos (all from the west)\nFlickr 2024+: 14 photos (west views, details)\narchitecture.com.au: both award galleries (20)\nsportsvenuebusiness: 5   marvelstadium.com.au: text only\n\nFound: no photo of the north end or the north-east side.\nThe 2019 aerial sees them edge-on or not at all.',fontsize=13,va='top',transform=ax2.transAxes)
for k,(f,t) in enumerate((('q_NE_.png','A: copy the matching side from across the ground (what the model does now).\nSeen from the north-east: the far side shows the near side flipped, sign reads backwards.'),
                          ('q_NE_own.png','B: leave the sides with no photo untextured (black) until photos exist.'))):
    axi=fig.add_axes([0.02+0.49*k,0.04,0.47,0.42]);axi.imshow(Image.open(f));axi.axis('off');axi.set_title(t,fontsize=12,loc='left')
plt.savefig(sys.argv[1]);print('ok')
