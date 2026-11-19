import json,cv2,numpy as np,sys
h=json.load(open('sat/her20.json'));c=h['c'];HS=h['HS']
top=cv2.imread(sys.argv[1] if len(sys.argv)>1 else 'sat/top.png',cv2.IMREAD_UNCHANGED)
PC=(0.94,-11.82)
x0=(c[0]-HS-(PC[0]-170))/0.2; y0=((PC[1]+170)-(c[1]+HS))/0.2
M=np.float32([[0.5,0,x0],[0,0.5,y0]])
cr=cv2.warpAffine(top,M,(1400,1400),flags=cv2.WARP_INVERSE_MAP|cv2.INTER_LINEAR)
sat=cv2.imread('sat/her20g.png')
if cr.shape[2]==4:
    a=cr[:,:,3:4]/255.0;rgb=cr[:,:,:3]
else: a=np.ones((1400,1400,1));rgb=cr
bl=(sat*(1-0.55*a)+rgb*0.55*a).astype(np.uint8)
# edges of model alpha / content
g=cv2.cvtColor(rgb,cv2.COLOR_BGR2GRAY);e=cv2.Canny(g,40,120)
ol=sat.copy();ol[e>0]=(0,0,255)
cv2.imwrite('sat/her_blend.png',bl);cv2.imwrite('sat/her_edge.png',ol)
