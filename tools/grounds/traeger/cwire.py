# club wireframe on a photo. python cwire.py aerial|w04 photo x0 y0 x1 y1 scale out
import sys,json,numpy as np,cv2
from cam import proj,load
mode,ph=sys.argv[1],sys.argv[2];x0,y0,x1,y1,sc=map(int,sys.argv[3:8]);out=sys.argv[8]
G=json.load(open('club_uv.json'))['G']+[g for g in json.load(open('stand.json'))['G'] if g['mat'] in('roof_top','fascia')]
if mode=='aerial':
    p=load();P=lambda X:proj(p,X)
else:
    c=json.load(open('cam_w04b.json'));K=np.array([[c['f'],0,c['w']/2],[0,c['f'],c['h']/2],[0,0,1.]])
    def P(X):
        q,_=cv2.projectPoints(np.array(X,float),np.array(c['r']),np.array(c['t']),K,None);return q[:,0]
im=cv2.imread(ph)[y0:y1,x0:x1];im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
COL={'roof_green':(0,255,0),'roof_blue_club':(255,128,0),'steel_white':(255,255,255),'club_brick':(0,200,255),'club_render':(0,255,255),'ac_unit':(255,0,255),'glass_bal':(255,255,0),'fascia':(0,0,255),'roof_top':(0,0,200)}
for g in G:
    col=COL.get(g['mat'],(128,128,128));q=P(g['V'])
    for f in g['F']:
        for i in range(len(f)):
            a=q[f[i]];b=q[f[(i+1)%len(f)]]
            cv2.line(im,(int((a[0]-x0)*sc),int((a[1]-y0)*sc)),(int((b[0]-x0)*sc),int((b[1]-y0)*sc)),col,1,cv2.LINE_AA)
cv2.imwrite(out,im)
