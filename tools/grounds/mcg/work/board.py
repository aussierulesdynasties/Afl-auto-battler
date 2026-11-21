# python work/board.py out "view:u:v[:half]" ... : gridded crops (labels every 10 px) tiled in a row-wrapped board
import sys,cv2,numpy as np
out=sys.argv[1];tiles=[]
for s in sys.argv[2:]:
    p=s.split(':');v=p[0];u,w=int(float(p[1])),int(float(p[2]));h=int(p[3]) if len(p)>3 else 50;S=int(p[4]) if len(p)>4 else 4
    im=cv2.imread(f'ge/{v}.png' if not v.endswith('.png') else v);u0,w0=max(u-h,0),max(w-h,0);c=im[w0:w+h,u0:u+h]
    c=cv2.resize(c,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
    for x in range((u0//10+1)*10,u+h,10):
        X=(x-u0)*S;cv2.line(c,(X,0),(X,c.shape[0]),(0,200,255) if x%50==0 else (0,110,140),1)
        if x%20==0: cv2.putText(c,str(x),(X+2,10),0,0.35,(0,255,255),1)
    for y in range((w0//10+1)*10,w+h,10):
        Y=(y-w0)*S;cv2.line(c,(0,Y),(c.shape[1],Y),(0,200,255) if y%50==0 else (0,110,140),1)
        if y%20==0: cv2.putText(c,str(y),(2,Y-2),0,0.35,(0,255,255),1)
    cv2.putText(c,v,(4,c.shape[0]-6),0,0.6,(0,0,255),2);tiles.append(c)
W=max(t.shape[1] for t in tiles);H=max(t.shape[0] for t in tiles);per=max(1,1800//W)
tiles=[np.pad(t,((0,H-t.shape[0]),(0,W-t.shape[1]),(0,0))) for t in tiles]
rows=[np.hstack(tiles[i:i+per]+[np.zeros_like(tiles[0])]*(per-len(tiles[i:i+per]))) for i in range(0,len(tiles),per)]
cv2.imwrite(out,np.vstack(rows))
