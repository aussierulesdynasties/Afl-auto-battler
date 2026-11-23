# sun.py YYYY-MM-DD AZ : sun elevation at Subiaco (lat -31.944) for a measured azimuth (deg from north, east positive), and local solar time
import sys,math,datetime
lat=math.radians(-34.880);d=datetime.date.fromisoformat(sys.argv[1]);az=float(sys.argv[2])
n=d.timetuple().tm_yday;g=2*math.pi/365*(n-1)
dec=0.006918-0.399912*math.cos(g)+0.070257*math.sin(g)-0.006758*math.cos(2*g)+0.000907*math.sin(2*g)-0.002697*math.cos(3*g)+0.00148*math.sin(3*g)
best=None
for i in range(-7200,7201):
    h=math.radians(i/40)   # hour angle, deg
    el=math.asin(math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(h))
    A=math.degrees(math.atan2(-math.sin(h),math.tan(dec)*math.cos(lat)-math.sin(lat)*math.cos(h)))%360
    e=abs((A-az+180)%360-180)
    if el>0 and (best is None or e<best[0]):best=(e,math.degrees(el),i/40/15+12)
print('elevation %.2f deg, cot %.4f, solar time %.2f h (az miss %.3f)'%(best[1],1/math.tan(math.radians(best[1])),best[2],best[0]))
