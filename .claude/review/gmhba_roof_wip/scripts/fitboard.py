import json,math,numpy as np
from PIL import Image,ImageDraw,ImageFont
exec(open('../w/fit3.py').read().split("th,t=0.0")[0])
F=json.load(open('fit3.json'));th,t=F['th'],np.array(F['t'])
S=2.4;X0,Y1=-150,150;im=Image.new('RGB',(int(290*S)+360,int(310*S)),(20,20,24));d=ImageDraw.Draw(im)
P2=lambda x,y:((x-X0)*S,(Y1-y)*S)
for w in W:d.point(P2(*w),fill=(0,220,255))
try:f=ImageFont.truetype('arial.ttf',13)
except:f=None
for k,(a,b,s,g) in P.items():
  for (tt,tv,col) in [((0.0),np.array([9.0,22.0]),(255,90,90)),(th,t,(80,255,80))]:
    m=tf(G[k],tt,tv);x,y=P2(*m);d.ellipse([x-4,y-4,x+4,y+4],outline=col,width=2)
  m=tf(G[k],th,t);x,y=P2(*m);d.text((x+6,y-6),f"{k} {F['r'][k]:+.1f}"+(' H' if k in F['hold'] else ''),fill=(255,255,255),font=f)
tx=int(290*S)+10;y=10
lines=['GMHBA frame fit (GE wall feet, point-to-line)',f'3-param: rot {math.degrees(th):+.2f} deg, model = lat0 - ({t[0]:.2f},{t[1]:.2f})','cyan = model wall base','red = GE pick under (+9,+22)','green = GE pick after fit','H = hold-out','','pt  side gap  before  after']
for k,(a,b,s,g) in P.items():lines.append(f"{k:10s}{s} {g:.2f} {F['r0'][k]:+6.2f} {F['r'][k]:+6.2f}{' H' if k in F['hold'] else ''}")
fr=[F['r'][k] for k in P if k not in F['hold']]
lines+=['',f'rms fit pts {math.sqrt(np.mean(np.square(fr))):.2f} m','RESULT: FAIL (rms>1, S_wall3 3.7 m)','Esri: W/S model pave corners under','roof or in plain sand: not pickable','all points GE-only']
for L in lines:d.text((tx,y),L,fill=(230,230,230),font=f);y+=17
im.save('gmhba_frame_fit_board.png')
