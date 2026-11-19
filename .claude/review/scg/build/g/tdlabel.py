import cv2,math
i=cv2.imread('sat/td_chamfer.png');H=170;px=0.2
def W2P(X,Y):return int((X-0.94+H)/px),int((-11.82+H-Y)/px)
for a0,a1,txt in((30,60,'ROOF LEAN (Messenger, 30-60 deg)'),(93,110,'ROOF LEAN (Messenger outer edge + stair core, 93-110 deg)')):
    for a in range(a0,a1+1):
        r=150;p=W2P(0.94+r*math.cos(math.radians(a)),-11.82+r*math.sin(math.radians(a)));cv2.circle(i,p,4,(255,0,255),-1)
    am=math.radians((a0+a1)/2);p=W2P(0.94+158*math.cos(am),-11.82+158*math.sin(am))
    cv2.putText(i,txt,((600,150) if a0==93 else (max(5,p[0]-330),max(30,p[1]))),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),6);cv2.putText(i,txt,((600,150) if a0==93 else (max(5,p[0]-330),max(30,p[1]))),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,0,255),2)
L=open('proof/topdown_numbers.txt').read().splitlines()
cv2.rectangle(i,(0,48),(575,60+20*len(L)),(20,20,20),-1);cv2.rectangle(i,(0,0),(900,44),(20,20,20),-1)
for k,l in enumerate(L):cv2.putText(i,l.strip(),(8,70+20*k),cv2.FONT_HERSHEY_SIMPLEX,0.45,(20,20,20),1);cv2.putText(i,l.strip(),(8,70+20*k),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,255,255),1)
cv2.putText(i,'green <1 m  yellow 1-2 m  red >2 m (distance to nearest satellite edge)',(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(20,20,20),1);cv2.putText(i,'green <1 m  yellow 1-2 m  red >2 m (distance to nearest satellite edge)',(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
cv2.imwrite('proof/topdown.png',i)
m=cv2.imread('shots/turn/mes_tip.png') if False else None
