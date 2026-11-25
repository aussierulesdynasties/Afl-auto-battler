import json,cv2,numpy as np
d=json.load(open('osm/geo.json'));G=d['geo'];N=1700;H=170.0;PC=np.array(G['4000006'])[:-1].mean(0)
im=cv2.imread('sat/sat_world.png')
def px(p):return (int((p[0]-PC[0]+H)/(2*H)*N),int((H-(p[1]-PC[1]))/(2*H)*N))
cols=[(0,0,255),(0,255,255),(255,0,255),(0,255,0),(255,128,0),(255,255,255)]
for i,(k,g) in enumerate(G.items()):
    if k[0]=='T':cv2.circle(im,px(g[0]),6,(0,0,255),2);continue
    pts=np.array([px(p) for p in g]);cv2.polylines(im,[pts],False,cols[i%6],2)
    cv2.putText(im,k[-4:],pts[0],0,0.6,cols[i%6],2)
cv2.imwrite('sat/osm_on_sat.png',im)
