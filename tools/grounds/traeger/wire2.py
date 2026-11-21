# wire2: draw stand.json through a fitpnp camera: python wire2.py cam.json photo out [scale]
import sys,json,numpy as np,cv2
c=json.load(open(sys.argv[1]));G=json.load(open('stand.json'))['G'];im=cv2.imread(sys.argv[2]);sc=float(sys.argv[4]) if len(sys.argv)>4 else 1
K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1.]])
COL={'fascia':(0,0,255),'banner':(255,255,0),'glass':(255,200,0),'cream_band':(255,255,128),'seat_white':(0,255,0),'seat_navy':(0,160,0),'steel_white':(255,255,255),'cable':(200,200,200),'stone':(0,200,255),'cladding':(80,80,255),'cream':(128,255,128),'roof_top':(0,0,255),'roof_soffit':(0,128,255),'roof_fascia':(0,0,255),'canopy':(255,0,255),'box_front':(255,255,0),'seats':(0,255,0),'plinth':(0,255,255),'lift':(255,128,0),'south_wall':(128,255,128)}
im=cv2.resize(im,None,fx=sc,fy=sc)
for m in G:
    if m['name'].startswith(('seat','riser','tread')) and m['name'] not in ('seat0_0',):
        if not m['name'].startswith('riser'):continue
    col=COL.get(m['mat'],(255,255,255))
    for f in m['F']:
        X=np.array([m['V'][i] for i in f],np.float64);Q=cv2.projectPoints(X,np.array(c['r']),np.array(c['t']),K,None)[0][:,0]*sc
        cv2.polylines(im,[Q.astype(np.int32)],True,col,1,cv2.LINE_AA)
cv2.imwrite(sys.argv[3],im)
