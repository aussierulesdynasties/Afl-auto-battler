import json,cv2,numpy as np
d=json.load(open('osm/geo.json'));G=d['geo'];h=json.load(open('sat/her20.json'))
c=h['c'];HS=h['HS'];m=h['mpp']
im=cv2.imread('sat/her20g.png')
def px(p):return (int((p[0]-c[0]+HS)/m),int((HS-(p[1]-c[1]))/m))
cols=[(0,0,255),(0,255,255),(255,0,255),(0,255,0),(255,128,0),(255,255,255)]
for i,(k,g) in enumerate(G.items()):
    if k[0]=='T':continue
    pts=np.array([px(p) for p in g])
    if ((pts>=0)&(pts<1400)).all(1).sum()<2:continue
    cv2.polylines(im,[pts],False,cols[i%6],2)
    cv2.putText(im,k,tuple(pts[0]),0,0.6,cols[i%6],2);print(k,len(g))
cv2.imwrite('sat/her_osm.png',im)
