import sys,os;sys.path.insert(0,os.getcwd())
from frame import *
from cam import proj
from scipy.optimize import least_squares
from PIL import Image,ImageDraw
G={'NW':(-90,51.7),'NE':(-101.25,-50),'SE':(61.25,-67),'SW':(73.75,30.5)}
Es={'NW':(-96,42.5),'NE':(-100,-58.75),'SE':(55,-77.5),'SW':(70,23.75)}
FL=np.array([543,230.]);FR=np.array([1295,223.])
LL=(np.array([543,230.]),np.array([413,350.]));LR=(np.array([1295,223.]),np.array([1413,350.]))
def pl(q,l):a,b=l;d=(b-a)/np.linalg.norm(b-a);v=q-a;return v[0]*d[1]-v[1]*d[0]
def pj(st,ds,dt,z):return proj(P,[wld(st[0]+ds,st[1]+dt,z)])[0]
def run(C,name):
    def r(x):
        ds,dt,z=x
        return np.r_[pj(C['NE'],ds,dt,z)-FL,pj(C['SE'],ds,dt,z)-FR,pl(pj(C['NW'],ds,dt,z),LL),pl(pj(C['SW'],ds,dt,z),LR)]
    f=least_squares(r,[0,0,47]);print(name,'ds %.2f dt %.2f z %.2f'%tuple(f.x),'res',np.round(f.fun,1))
    return f.x
xg=run(G,'google');xe=run(Es,'esri')
# also fixed z=47.9 (deck) variant
for C,n in((G,'google'),(Es,'esri')):
    f=least_squares(lambda x:np.r_[pj(C['NE'],*x,47.9)-FL,pj(C['SE'],*x,47.9)-FR,pl(pj(C['NW'],*x,47.9),LL),pl(pj(C['SW'],*x,47.9),LR)],[0,0])
    print(n,'z47.9 ds %.2f dt %.2f'%tuple(f.x),np.round(f.fun,1))
im=Image.open('mu.png').convert('RGB');d=ImageDraw.Draw(im)
for C,x,col in((G,xg,(255,0,0)),(Es,xe,(0,255,255))):
    q=[tuple(pj(C[k],*x)) for k in('NW','NE','SE','SW')];d.polygon(q,outline=col)
im.crop((300,150,1550,450)).save('../sat/fitroof.jpg')
