# texture board: each hand-made texture (out/tex) beside a photo crop of the same surface. python texboard.py out.png
import cv2,numpy as np,sys
L='refs5/SCG-ladies-members-stands.jpg';P63='refs3/063.jpg';P101='refs3/101.jpg'
ROWS=[('roof (Messenger blade)','roof',P63,(760,150,880,230)),
      ('glassroof (Messenger glazing)','glassroof',P63,(588,150,640,215)),
      ('podium (Messenger podium)','podium',P63,(790,560,900,620)),
      ('sbback (scoreboard back)','sbback',P63,(470,615,580,690)),
      ('tower (light tower, green steel)','tower',P63,(674,480,694,640)),
      ('seat (bowl, teal)','seat',P101,(110,290,260,340)),
      ('seathM (Members, maroon)','seathM',L,(652,560,760,582)),
      ('hroof (heritage green roof)','hroof',L,(260,478,420,505)),
      ('brick (Members end)','brick','refs3/053.jpg',(165,235,200,262)),
      ("glasst (Trumper/O'Reilly back glass)",'glasst','refs3/144.jpg',(500,70,700,140)),
      ('facade (white top cladding)','facade','refs3/144.jpg',(450,28,700,55)),
      ('dark (under-deck band)','dark','refs3/134.jpg',(20,165,150,215)),
      ('wall (pale concrete faces)','wall','refs3/005.jpg',(208,323,433,350)),
      ('conc (columns)','conc','refs3/005.jpg',(243,350,258,398)),
      ('roofu (roof underside)','roofu','refs3/134.jpg',(200,30,330,130)),
      ('hw115 (heritage brick wall)','hw115','refs3/053.jpg',(290,195,365,255))]
H=220;rows=[]
for lab,tx,ph,(x0,y0,x1,y1) in ROWS:
    p=cv2.imread(ph)[y0:y1,x0:x1];p=cv2.resize(p,(int(p.shape[1]*H/p.shape[0]),H),interpolation=cv2.INTER_CUBIC)
    if p.shape[1]>420:p=p[:,:420]
    t=cv2.imread('out/tex/%s.png'%tx);t=t[:min(t.shape[0],t.shape[1]),:min(t.shape[0],t.shape[1])];t=cv2.resize(t,(H,H))
    row=np.full((H+34,900,3),255,np.uint8);row[30:30+H,4:4+p.shape[1]]=p;row[30:30+H,440:440+H]=t
    cv2.putText(row,lab+'  -  photo | hand-made texture',(6,22),0,0.55,(0,0,0),2);rows.append(row)
cv2.imwrite(sys.argv[1],np.vstack(rows))
