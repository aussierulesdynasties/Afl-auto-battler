# apron check: photo vs render mean colour (7x7 px, 1023 frame) at traced ground points (s, d), on the model surface
exec(open('pj.py',encoding='utf-8').read())
ZGK=np.array([(0,0),(95,0),(110,4.5),(128,4.5),(140,4.5),(160,7),(175,11),(197,11),(201,11.5),(214,8.8),(220,8.33),(225,8.5),(235,9),(245,6),(320,5),(380,10),(400,10),(415,0),(PER,0)],float)
def ZG(s):return 10.0 if 136<=s<170 else float(np.interp(s%PER,ZGK[:,0],ZGK[:,1]))
def zs(s,d):z0=float(np.interp(s%PER,ZGK[:,0],ZGK[:,1]));return z0 if d<=45 else max(0.0,z0-(d-45)/2)
IP_=np.asarray(Image.open('ref.jpg').convert('RGB').resize((1023,576),Image.LANCZOS),float)
RR_=np.asarray(Image.open('out/render.png').convert('RGB').resize((1023,576),Image.LANCZOS),float)
PTS=[('ring dirt',150,42),('ring dirt',165,43),('slope dirt',170,50),('slope dirt',176,54),('slope grass',150,52),('plaza asph',192,52),('plaza asph',198,58),
     ('ring asph',215,42),('ring asph',235,43),('road asph',220,46.5),('grass',220,56),('grass',235,58),('grass',212,54)]
for nm,s,d in PTS:
    z=zs(s,d) if not(136<=s<170 and d<39.5) else 10.0
    p=proj(P([s],d,z)[0])[0];x,y=int(round(p[0])),int(round(p[1]))
    if not(3<=x<1020 and 3<=y<573):print(nm,s,d,'off frame');continue
    a=IP_[y-3:y+4,x-3:x+4].reshape(-1,3).mean(0);b=RR_[y-3:y+4,x-3:x+4].reshape(-1,3).mean(0)
    print('%-11s s%3d d%4.1f  photo %s render %s  diff %d'%(nm,s,d,a.astype(int),b.astype(int),int(np.abs(a-b).mean())))
