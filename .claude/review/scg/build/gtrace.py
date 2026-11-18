exec(open('meas.py').read())
from PIL import Image
from scipy import ndimage as nd
hsv=np.array(Image.open('refs/scg.jpg').convert('HSV')).astype(int)
gr=(hsv[...,0]>60)&(hsv[...,0]<110)&(hsv[...,1]>80)&(hsv[...,2]>70)
gr=nd.binary_opening(gr,iterations=1)
c0=pr([(*PC,0)])[0]
for k in ['195513202','195513198']:
    P=polar(G[k])
    for ad in range(112,170,3):
        a=math.radians(ad);i=ad*2;lo,hi=P[i]
        if np.isnan(lo):continue
        # for z values, project inner-edge point and see if green there; find lowest z where inner pt lands on green boundary
        res=[]
        for z in np.arange(0,40,0.5):
            for nm,r in (('in',lo),('out',hi)):
                X=PC+r*np.array([math.cos(a),math.sin(a)]);u,v=pr([(*X,z)])[0]
                if 0<=u<1200 and 0<=v<675:res.append((nm,z,int(gr[int(v),int(u)])))
        ins=[z for nm,z,g in res if nm=='in' and g];outs=[z for nm,z,g in res if nm=='out' and g]
        print(k,ad,'r %.0f-%.0f'%(lo,hi),'inner green z',(min(ins),max(ins)) if ins else None,'outer green z',(min(outs),max(outs)) if outs else None)
