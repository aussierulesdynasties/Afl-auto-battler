p='build5.py';s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a[:60];s=s.replace(a,b)
rep("prism([(-105.2,46.1),(-99.7,60.1),(-86,56),(-92,40)],0,21.5,DARK,DARK)\n",
"""prism([(-105.2,46.1),(-99.7,60.1),(-86,56),(-92,40)],0,21.5,DARK,DARK)
# lower front-right wing of the dark block on the podium roof, carrying the S1 tower (photo corners unprojected at z 10.6/16)
prism([(-105.2,46.1),(-96.5,29.2),(-90.7,27.0),(-91.5,40.0)],10.6,16.0,DARK,DARK)
# rooftop plant on the dark block (positions read off the photo grid, unprojected at z 21.5): units, ducts, parapet
for (px_,py_,ex,ey,ez,a_) in [(-91.4,56.0,1.6,1.1,0.9,0.37),(-97.0,50.0,2.4,1.3,1.0,0.37),(-93.6,46.0,1.8,1.2,0.8,0.37),
                             (-100.6,53.0,1.4,1.0,0.7,0.37),(-96.0,44.0,1.2,0.9,1.1,0.37),(-99.8,47.8,1.0,1.0,0.6,0.37)]:
    obox((px_,py_,21.5+ez),ex,ey,ez,a_,CONC)
cyl((-95.5,57.5,21.5),(-95.5,57.5,23.2),0.9,0.9,CONC,12);cyl((-89.5,50.5,21.5),(-89.5,50.5,22.8),0.7,0.7,CONC,12)
cyl((-98.5,55.0,22.3),(-92.0,48.0,22.3),0.35,0.35,CONC,8);cyl((-101.0,51.0,22.0),(-95.0,45.0,22.0),0.3,0.3,CONC,8)
""")
i0=s.index("prism([(-98.9,-48.0)");i1=s.index("dr=[];cx,cy_,rr")
s=s[:i0]+"""# SE outbuildings, roofs read off the photo grid and unprojected at z 3 (photo: low flat-roofed blocks, ~3 m)
prism([(-93.5,-46.3),(-84.7,-68.6),(-92.5,-77.7),(-105.5,-78.0),(-110.8,-69.5),(-111.6,-62.2),(-99.1,-61.2),(-98.3,-68.7),(-110.8,-69.5)][:6]+[(-112.6,-48.1)],0,3.0,WHITE,WHITE)
obox((-105.2,-65.6,3.6),3.2,2.6,0.6,math.radians(-80),DARK)
prism([(-66.7,-93.0),(-65.1,-108.0),(-74.8,-116.1),(-79.7,-113.4),(-81.3,-99.2),(-74.8,-93.9)],0,3.0,WHITE,WHITE)
cyl((-66.0,-112.5,0),(-66.0,-112.5,5.0),2.2,2.2,DARK,24)
# white fabric-roof building: dark walls to 3 m, domed membrane to 6.5 m (outline unprojected at z 3)
DOME=[(-100.8,-99.7),(-94.9,-104.9),(-93.9,-113.7),(-98.6,-119.1),(-109.3,-120.3),(-116.3,-110.8),(-114.7,-104.8),(-106.9,-100.0)]
prism(DOME,0,3.0,DARK,DARK)
dc=Vector((sum(p[0] for p in DOME)/8,sum(p[1] for p in DOME)/8,0));rings=[]
for k in range(6):
    t=k/5;rr_=math.cos(t*math.pi/2);zz=3.0+3.5*math.sin(t*math.pi/2)
    rings.append([bm.verts.new((dc.x+(p[0]-dc.x)*rr_,dc.y+(p[1]-dc.y)*rr_,zz)) for p in DOME])
for k in range(5):
    for j in range(8):face([rings[k][j],rings[k][(j+1)%8],rings[k+1][(j+1)%8],rings[k+1][j]][::-1],ROOF)
"""+s[i1:]
rep("# yellow raking columns under", """# white ribs across the navy strip at every lobe dip
for a in R[1:-1]:
    nf=NAVYW/max(1.0,rout(a)-rin(a)+NAVYW);cyl(rp(a,0.0,0.08),rp(a,nf,0.08),0.14,0.14,WHITE,6)
# yellow raking columns under""")
# voms reach down to the walkway (photo: openings run to the walkway, tops unchanged)
rep("F=T(a,0.15);zt=F.z+2.4;B=T(a,0.15+2.4/(6.7/11.62))","Ft=T(a,0.15);zt=Ft.z+2.4;F=Vector((Ft.x,Ft.y,6.0));B=T(a,0.15+2.4/(6.7/11.62))")
rep("xs=[-1.5,-0.9,0.9,1.5];MS=[WHITE,DARK,WHITE];HD=[WHITE,RED,WHITE]","xs=[-1.5,-0.9,0.9,1.5];MS=[CONC,DARK,CONC];HD=[CONC,RED,CONC]")
open(p,'w',encoding='utf-8',newline='').write(s)
