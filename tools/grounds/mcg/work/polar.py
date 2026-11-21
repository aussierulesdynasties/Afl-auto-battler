# python work/polar.py idrender.png outprefix : unroll Esri sat to bearing x radius (r 60..200 m, 0.25 m/row, 8 px/deg); top = sat, bottom = sat + model lines
# cyan = model silhouette, yellow = roof edges, magenta = screens/canopy edges, red = facade-wall top edge
import sys,cv2,numpy as np,hashlib
S=cv2.imread('sat/esri_025.png');r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED);out=sys.argv[2]
def srgb(x):x=x/255.;return np.where(x<=0.0031308,x*12.92,1.055*x**(1/2.4)-0.055)*255
def idc(n):h=hashlib.md5(n.encode()).digest();return srgb(np.array([h[2],h[1],h[0]],float))
col=r[:,:,:3].astype(float);al=r[:,:,3]>128
def mask(names):
    m=np.zeros(al.shape,bool)
    for n in names:m|=(np.abs(col-idc(n)).sum(2)<9)&al
    return m.astype(np.uint8)
def edge(m):return m-cv2.erode(m,np.ones((3,3),np.uint8))
roof=mask(['roof_white','roof_grey','roof_teal','roof_clear_w','roof_fascia','fascia','steel_blue','steel_white','trusses'])
roof=cv2.morphologyEx(roof,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
scr=mask(['screen','screens','steel_dark','paint_white'])
L={'sil':edge(al.astype(np.uint8)),'roof':edge(roof),'scr':edge(scr)}
print({k:int(v.sum()) for k,v in L.items()})
def unroll(img,b0,b1,interp):
    bs=np.arange(b0,b1,1/8);rs=np.arange(200,60,-0.25)
    B,R=np.meshgrid(np.radians(bs),rs);X=(R*np.sin(B)+260)*4;Y=(260-R*np.cos(B))*4
    return cv2.remap(img,X.astype(np.float32),Y.astype(np.float32),interp)
def grid(s,b0):
    for i,rr in enumerate(range(200,61,-5)):
        y=i*20;s[y]=s[y]//2+(70 if rr%25 else 150)
        if rr%10==0:cv2.putText(s,str(rr),(2,y+12),0,0.4,(0,255,255),1)
    for k in range(0,720,16):
        s[:,k]=s[:,k]//2+(70 if k%80 else 150)
        if k%80==0:cv2.putText(s,str(b0+k//8),(k+2,555),0,0.45,(0,255,255),1)
for b0 in range(0,360,45):
    s=unroll(S,b0,b0+90,cv2.INTER_LINEAR);t=s.copy()
    for k,c in (('scr',(255,0,255)),('roof',(0,230,255)),('sil',(255,255,0))):
        t[unroll(L[k],b0,b0+90,cv2.INTER_NEAREST)>0]=c
    grid(s,b0);grid(t,b0);cv2.imwrite(f'{out}_{b0:03d}.png',np.vstack([s,t]))
