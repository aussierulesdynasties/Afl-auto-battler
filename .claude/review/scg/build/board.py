# crop board: per part, photo | render | 50/50 overlay at 2x, labelled.  python board.py photo render out "name:x0,y0,x1,y1" ...
import cv2,numpy as np,sys
ph=cv2.imread(sys.argv[1]);r=cv2.imread(sys.argv[2],cv2.IMREAD_UNCHANGED);a=r[:,:,3:4]/255.0
comp=(r[:,:,:3]*a+ph*(1-a)).astype(np.uint8);ov=cv2.addWeighted(ph,0.5,comp,0.5,0);rows=[]
for spec in sys.argv[4:]:
    n,b=spec.split(':');x0,y0,x1,y1=map(int,b.split(','));k=max(1,int(600/(x1-x0)))
    tiles=[cv2.resize(im[y0:y1,x0:x1],None,fx=k,fy=k,interpolation=cv2.INTER_NEAREST) for im in (ph,comp,ov)]
    row=np.hstack([np.pad(t,((30,6),(3,3),(0,0)),constant_values=255) for t in tiles])
    for j,l in enumerate(('photo','model','overlay')):cv2.putText(row,f'{n} - {l}',(8+j*(tiles[0].shape[1]+6),22),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),2)
    rows.append(row)
w=max(x.shape[1] for x in rows);cv2.imwrite(sys.argv[3],np.vstack([np.pad(x,((0,0),(0,w-x.shape[1]),(0,0)),constant_values=255) for x in rows]))
