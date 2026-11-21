# Radial profiles of the surface model: for each bearing, median z in 1 m radial bins (r 60..200). Writes an image
# with bearings as rows, radius as columns, colour = height, plus the roof edges found by threshold.
import sys,numpy as np,cv2
d=np.load(sys.argv[1]);z=d['z'].astype(np.float32);s=d['score'];res=float(d['res']);x0=float(d['x0']);y1=float(d['y1'])
z=cv2.medianBlur(z,5);z[s<0.25]=np.nan
B=np.arange(0,360,2.0);R=np.arange(50,200,1.0);P=np.full((len(B),len(R)),np.nan)
for i,b in enumerate(B):
    for j,r in enumerate(R):
        vals=[]
        for db in (-0.8,0,0.8):
            a=np.radians(b+db)
            for dr in (-0.4,0.4):
                x=(r+dr)*np.sin(a);y=(r+dr)*np.cos(a);c=int((x-x0)/res);w=int((y1-y)/res)
                if 0<=w<z.shape[0] and 0<=c<z.shape[1]: vals.append(z[w,c])
        P[i,j]=np.nanmedian(vals) if np.any(~np.isnan(vals)) else np.nan
np.save(sys.argv[2],P)
v=cv2.applyColorMap(np.clip((np.nan_to_num(P)+6)/60*255,0,255).astype(np.uint8),cv2.COLORMAP_JET)
v=cv2.resize(v,None,fx=4,fy=4,interpolation=cv2.INTER_NEAREST)
for r in range(50,200,10): cv2.line(v,((r-50)*4,0),((r-50)*4,v.shape[0]),(255,255,255),1);cv2.putText(v,str(r),((r-50)*4+2,10),0,0.35,(255,255,255),1)
for b in range(0,360,30): cv2.line(v,(0,b*2),(v.shape[1],b*2),(255,255,255),1);cv2.putText(v,str(b),(2,b*2-2),0,0.35,(255,255,255),1)
cv2.imwrite(sys.argv[3],v)
