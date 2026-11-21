# draw height rulers (0..90 m, tick 5 m) at plan points into GE view images. Usage: ruler.py view x,y x,y ...
import sys,os,cv2,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import earthcam as E
Z0=float(os.environ.get('Z0','0'))
def cam(v):
    h=int(v[1:]); d,t={'l':(520,65),'o':(900,45),'n':(330,78)}[v[0]]; return E.cam(h,t,d,tz=0.0)
def P(v,X): X=np.array(X,float); X[2]+=Z0; return E.proj(cam(v),X)
if __name__=='__main__':
    v=sys.argv[1]; im=cv2.imread(f'ge/{v}.png')
    for s in sys.argv[2:]:
        x,y=map(float,s.split(','))
        for z in range(0,91,5):
            a=P(v,[x,y,z]); c=(0,255,255) if z%10==0 else (0,0,255)
            cv2.circle(im,(int(a[0]),int(a[1])),3 if z%10 else 4,c,-1)
            if z%20==0: cv2.putText(im,str(z),(int(a[0])+5,int(a[1])),0,0.45,(255,255,255),1)
    cv2.imwrite(f'ge/r_{v}.png',im)
