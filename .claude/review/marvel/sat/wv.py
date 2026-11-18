import sys,os;sys.path.insert(0,os.getcwd())
from frame import *
from cam import R as Rm
from PIL import Image
c=json.load(open(sys.argv[1]));p=c['p'];k=np.array(c['k']);z=float(sys.argv[2]);out=sys.argv[3]
A=np.asarray(Image.open('../sat/lplan_all_clean.png').convert('RGB'))
u,v=np.meshgrid(np.arange(1920)+.5,np.arange(1080)+.5)
M=Rm(*p[3:6]);d=np.stack([(u-p[7])/p[6],-(v-p[8])/p[6],np.ones_like(u)],-1)@M
C=np.array(p[:3]);tt=(z-C[2])/d[...,2];X=C+tt[...,None]*d
st=loc(X.reshape(-1,3)).reshape(1080,1920,2)+k*z
x=((200-st[...,1])*4).astype(int);y=((st[...,0]+200)*4).astype(int);ok=(x>=0)&(x<1600)&(y>=0)&(y<1600)&(tt>0)
W=np.zeros((1080,1920,3),np.uint8);W[ok]=A[y[ok],x[ok]]
mu=np.asarray(Image.open('mu.png').convert('RGB'))
Image.fromarray((0.5*mu+0.5*W).astype(np.uint8)).save(out,quality=85)
