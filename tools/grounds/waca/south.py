# Lillee-Marsh stand (south, far side of the 1992 photo). exec'd by build.py.
# Plan: fence/back curves; ends read off p92 (east x 48; west end oblique: x -22 at the fence, -10 at the back).
# Heights: p92 columns u 1650-1900 (v 455-465 roof fascia, 465-510 upper tier, 510-525 deck fascia,
# 525-550 shaded lower seats, 550-575 green seats, 575 fence).
def yf(x):return -69.2-0.025*x+0.00338*x*x          # field fence along the stand
def yb(x):return -102.0-0.0131*x+0.001548*x*x       # back wall
XE,XWF,XWB,DB=48.0,-22.0,-10.0,40.0
NS=32
def SP(t,d,z):
    x=XE+((XWF-XE)+((XWB-XE)-(XWF-XE))*min(d,DB)/DB)*t
    return (x,max(yb(x),yf(x)-d),z)
SEC=[('white',[(0,0),(0,1.2)]),
     ('greenseat',[(0.3,1.2),(7.0,4.6)]),('greenseat',[(7.0,4.6),(16.0,8.0)]),
     ('dark',[(16.0,8.0),(16.0,8.5)]),
     ('white',[(7.0,8.5),(7.0,10.5)]),('concrete',[(7.0,8.5),(16.0,8.5)]),
     ('navyseat',[(7.1,10.5),(DB,15.8)]),
     ('white',[(2.0,15.8),(2.0,17.7)]),('loft',[(2.0,15.8),(DB,16.5)]),('roof',[(2.0,17.7),(DB,17.7)])]
for i in range(NS):
    ta,tb=i/NS,(i+1)/NS
    for m,((d0,z0),(d1,z1)) in SEC:
        quad(m,[SP(ta,d0,z0),SP(tb,d0,z0),SP(tb,d1,z1),SP(ta,d1,z1)])
    quad('concrete',[SP(ta,99,0),SP(tb,99,0),SP(tb,99,17.7),SP(ta,99,17.7)])
for t in (0.0,1.0):
    quad('white',[SP(t,0,0),SP(t,0,1.2),SP(t,7,4.6),SP(t,7,10.5),SP(t,DB,15.8),SP(t,99,15.8),SP(t,99,0)])
    quad('white',[SP(t,2,15.8),SP(t,99,15.8),SP(t,99,17.7),SP(t,2,17.7)])
# raised roof (photo u 1690-1955, top v 428): x 1..38 from y -82 to the back, top 21.0 m
xs=[38-37*i/11 for i in range(12)]
for i in range(11):
    xa,xb=xs[i],xs[i+1]
    quad('roof',[(xa,-82,21.0),(xb,-82,21.0),(xb,yb(xb),21.0),(xa,yb(xa),21.0)])
    quad('white',[(xa,-82,17.7),(xb,-82,17.7),(xb,-82,21.0),(xa,-82,21.0)])
for x in (38,1):quad('white',[(x,-82,17.7),(x,yb(x),17.7),(x,yb(x),21.0),(x,-82,21.0)])
# A-frame roof frames (photo u 1570-1640 and 1930-2010, v 432-447)
for x in (46.0,40.0,-17.0,-21.0):
    y0=yf(x);p0,p1,ap=(x,y0-4,17.8),(x,y0-10,17.8),(x,y0-7,20.8)
    for b in (p0,p1):quad('yellow',[(b[0]-0.2,b[1],17.8),(b[0]+0.2,b[1],17.8),(ap[0]+0.2,ap[1],20.8),(ap[0]-0.2,ap[1],20.8)])
# vomitories through the green seats (photo u 1595/1660/1740/1820/1930): white side walls, dark opening
for x in (40.5,30.0,16.5,4.0,-12.0):
    y0=yf(x)
    for dx in (-0.9,0.9):quad('white',[(x+dx,y0-1.0,1.2),(x+dx,y0-7.0,4.6),(x+dx,y0-7.0,5.6),(x+dx,y0-1.0,2.2)])
    quad('dark',[(x-0.9,y0-1.05,1.2),(x+0.9,y0-1.05,1.2),(x+0.9,y0-1.05,2.2),(x-0.9,y0-1.05,2.2)])
# west end stair tower (photo u 2015-2060, base v 600, top v 480) and its flight down to the fence
boxpts('white',[(-20.5,-84.0),(-26.5,-84.0),(-26.5,-90.5),(-20.5,-90.5)],0,18.5,top='concrete')
for z in (3.5,7.0,10.5,14.0):quad('yellow',[(-20.5,-83.9,z),(-26.5,-83.9,z),(-26.5,-83.9,z+0.4),(-20.5,-83.9,z+0.4)])
quad('white',[(-20.5,-84.0,14.0),(-22.5,-84.0,14.0),(-20.5,-69.5,0.0),(-18.5,-69.5,0.0)])
