p='build5.py';s=open(p,encoding='utf-8',newline='').read()
i0=s.index("def lamphead(x,y,h,ang):");i1=s.index("# scoreboard (north end)")
new='''def lamphead(x,y,h,ang):
    # deep lattice cage measured from the photo: front frame of lamp shelves, back frame 3 m behind with
    # cross-braced bays, depth members at every shelf; sits 3.5 m lower than before (photo grid, 4 heads)
    fwd=Vector((math.cos(ang),math.sin(ang),0));side=Vector((-math.sin(ang),math.cos(ang),0));up=Vector((0,0,1))
    tl=math.radians(20);fz=fwd*math.cos(tl)-up*math.sin(tl);uz=up*math.cos(tl)+fwd*math.sin(tl)
    C=Vector((x,y,h-5.5-HDROP))+fwd*0.9
    def pt(sx,sz,sd=0.0):return C+side*sx+uz*sz+fz*sd
    def bar(a,b,r=0.13,m=TW):cyl(a,b,r,r,m,6)
    H2=5.4;wt,wb=6.8,5.6;DEP=3.0
    hw=lambda z:wb+(wt-wb)*(z+H2)/(2*H2)
    NS=6;zs=[-H2+k*(2*H2)/NS for k in range(NS+1)]
    for sd in (0.0,-DEP):
        bar(pt(-wb,-H2,sd),pt(-wt,H2,sd),0.18);bar(pt(wb,-H2,sd),pt(wt,H2,sd),0.18)
        for z in zs:bar(pt(-hw(z),z,sd),pt(hw(z),z,sd),0.15 if sd==0.0 else 0.13)
    # back face: 4 verticals and X-bracing in every bay
    fr=[-1,-0.5,0,0.5,1]
    for f_ in fr[1:-1]:bar(pt(f_*wb,-H2,-DEP),pt(f_*wt,H2,-DEP))
    for k in range(NS):
        z0,z1=zs[k],zs[k+1]
        for j in range(len(fr)-1):
            a0,a1=fr[j],fr[j+1]
            bar(pt(a0*hw(z0),z0,-DEP),pt(a1*hw(z1),z1,-DEP),0.1);bar(pt(a1*hw(z0),z0,-DEP),pt(a0*hw(z1),z1,-DEP),0.1)
    # depth members at every shelf end and the middle, diagonals on the two sides
    for z in zs:
        for f_ in (-1,0,1):bar(pt(f_*hw(z),z,0),pt(f_*hw(z),z,-DEP),0.11)
    for k in range(NS):
        for sx in (-1,1):bar(pt(sx*hw(zs[k]),zs[k],0),pt(sx*hw(zs[k+1]),zs[k+1],-DEP),0.09)
    for i in range(NS):
        z=(zs[i]+zs[i+1])/2;w=hw(z)-0.3
        obox(pt(0,zs[i]+0.1,-0.9),w,0.9,0.07,ang+math.pi/2,TW,tilt=-tl)
        n=8 if i<2 else 10
        for j in range(n):
            sx=-w+0.45+j*(2*w-0.9)/(n-1);p0=pt(sx,z,-1.2);p1=pt(sx,z,0.25)
            cyl(p0,p1,0.36,0.42,LAMP,10)
HDROP=3.5
# towers: thick white shafts (photo grid: 3.1-3.5 m across), lamp cage on top; measured base for the S1 tower
TPOS={(-92.8,36.1):(-92.8,34.2)}
for x,y,h in D['towers']:
    x,y=TPOS.get((x,y),(x,y))
    hb=h-5.5-HDROP;cyl((x,y,0),(x,y,hb),1.75,1.55,TW,20);cyl((x,y,0),(x,y,2.0),2.3,2.2,CONC,20)
    ang=math.atan2(-y,-x);lamphead(x,y,h,ang)
'''
s=s[:i0]+new+s[i1:]
open(p,'w',encoding='utf-8',newline='').write(s)
