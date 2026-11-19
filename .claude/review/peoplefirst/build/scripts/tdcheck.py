# zoom tiles every 30 deg: satellite with the model's straight-down silhouette edge (magenta) and a 50% blend. 2 m ticks.
import sys,json,numpy as np,cv2
S=json.load(open('sat.json'));m=S['mpp'];W=1000;Z=4
sat=cv2.imread('sat.png');x0,y0=int(round(S['px']-W/2)),int(round(S['py']-W/2));c=sat[y0:y0+W,x0:x0+W]
td=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);al=td[...,3:]/255.0
cb=cv2.resize(c,None,fx=Z,fy=Z,interpolation=cv2.INTER_CUBIC);ab=cv2.resize(al,None,fx=Z,fy=Z)[...,None]
tb=cv2.resize(td[...,:3],None,fx=Z,fy=Z);bl=(cb*(1-0.45*ab)+tb*0.45*ab).astype(np.uint8)
e=cv2.morphologyEx((ab[...,0]>0.5).astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8))>0;bl[e]=(255,0,255)
H=int(25/m*Z);tiles=[]
for ang in range(0,360,30):
    t=np.radians(ang);r=float(sys.argv[3]) if len(sys.argv)>3 else 108;u=int((W/2+r*np.cos(t)/m)*Z);v=int((W/2-r*np.sin(t)/m)*Z)
    z=bl[max(0,v-H):v+H,max(0,u-H):u+H].copy();z=cv2.copyMakeBorder(z,0,2*H-z.shape[0],0,2*H-z.shape[1],cv2.BORDER_CONSTANT)
    for gg in range(0,2*H,int(2/m*Z)):cv2.line(z,(gg,0),(gg,6 if (gg//int(2/m*Z))%5 else 16),(0,255,255),2)
    cv2.putText(z,str(ang),(20,40),0,1.2,(0,255,255),2);tiles.append(cv2.resize(z,(600,600)))
rows=[np.concatenate(tiles[i:i+4],1) for i in range(0,12,4)];cv2.imwrite(sys.argv[2],np.concatenate(rows,0))
