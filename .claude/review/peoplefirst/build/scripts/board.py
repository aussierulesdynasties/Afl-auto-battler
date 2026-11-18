# Gate boards: full-res photo | render | 50% overlay, and one crop row per part (3 panels, 3x pixel scale, nearest).
import cv2,numpy as np,sys
rp=sys.argv[1];ph=cv2.imread('photo_clean.png');r=cv2.imread(rp,cv2.IMREAD_UNCHANGED)
a=r[:,:,3:4]/255.0;ren=(r[:,:,:3]*a+ph*0*(1-a)+np.array([60,60,60])*(1-a)).astype(np.uint8)   # empty = flat grey (no photo)
ov=(ph*0.5+ren*0.5).astype(np.uint8)
def lab(im,t):
    im=im.copy();cv2.rectangle(im,(0,0),(14*len(t)+20,40),(0,0,0),-1);cv2.putText(im,t,(8,30),0,0.9,(255,255,255),2);return im
cv2.imwrite('gate/full_photo.png',ph);cv2.imwrite('gate/full_render.png',ren);cv2.imwrite('gate/full_overlay50.png',ov)
cv2.imwrite('gate/full_board.jpg',np.vstack([lab(ph,'photo'),lab(ren,'render'),lab(ov,'50% overlay')]),[cv2.IMWRITE_JPEG_QUALITY,92])
PARTS={'roof_north':(650,330,1650,560),'upper_stand_voms':(700,420,1500,560),'led_fascia_walkway':(720,510,1450,590),
'lower_bowl_west':(430,540,820,790),'roof_south':(400,720,1450,980),'podium_facade':(420,850,1100,1180),
'dark_block_red_drum':(500,860,1100,1020),'yellow_columns_se':(1100,850,1700,1100),'scoreboard':(410,490,530,650),
'tower_heads_w_e':[(270,440,340,520),(1580,370,1650,450)],'tower_heads_s':[(620,680,730,780),(1290,690,1400,790)],'se_buildings':(1130,960,1620,1110)}
rows=[]
for nm,bx in PARTS.items():
    bxs=bx if isinstance(bx,list) else [bx];row=[]
    for (x0,y0,x1,y1) in bxs:
        s=max(1,min(6,900//(x1-x0)))
        for im,t in ((ph,'photo'),(ren,'render'),(ov,'overlay')):
            c=cv2.resize(im[y0:y1,x0:x1],None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST);row.append(lab(c,f'{nm} {t} x{s}'))
    h=max(c.shape[0] for c in row);row=[cv2.copyMakeBorder(c,0,h-c.shape[0],0,6,cv2.BORDER_CONSTANT,value=(30,30,30)) for c in row]
    out=np.hstack(row);cv2.imwrite(f'gate/part_{nm}.png',out);rows.append(out)
W=max(x.shape[1] for x in rows);rows=[cv2.copyMakeBorder(x,0,8,0,W-x.shape[1],cv2.BORDER_CONSTANT,value=(30,30,30)) for x in rows]
big=np.vstack(rows);f=min(1.0,3000/big.shape[1]);cv2.imwrite('gate/parts_board.jpg',cv2.resize(big,None,fx=f,fy=f,interpolation=cv2.INTER_AREA),[cv2.IMWRITE_JPEG_QUALITY,90])
print(big.shape)
