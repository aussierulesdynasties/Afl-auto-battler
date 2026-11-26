import json,cv2,numpy as np
T=json.load(open('sat/trace.json'));Mo=json.load(open('sat/model.json'))
u=cv2.imread('sat/polar_sat.png');u=cv2.resize(u,(1440,1000),interpolation=cv2.INTER_NEAREST)  # 4 px/deg, 8 px/m
Y=lambda r:int((r-50)*8)
def dot(d,r,c):
    if r is None:return
    cv2.circle(u,(int(((d%360))*4),Y(r)),2,c,-1)
for i in range(720):
    dot(i/2,T['grass'][i],(0,255,0));dot(i/2,T['win'][i],(255,0,255));dot(i/2,T['wout'][i],(255,0,255))
    g=Mo['g'][i];dot(i/2,g+2.5 if g else None,(0,0,255))
for k,(a0,a1,rf,ro) in Mo['stands'].items():
    for j,(a,b) in enumerate(zip(rf,ro)):
        d=a0+j*0.5;dot(d,a,(0,140,255));dot(d,b,(0,140,255))
cv2.imwrite('sat/cmp.png',u)
for s in range(4):cv2.imwrite('sat/cmp%d.png'%s,u[:,s*360:(s+1)*360+40])
