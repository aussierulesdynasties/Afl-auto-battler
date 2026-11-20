import math,datetime
def sunpos(t):
    lat=math.radians(-42.868);lon=147.316
    n=(t-datetime.datetime(2000,1,1,12)).total_seconds()/86400
    L=math.radians((280.46+0.9856474*n)%360);g=math.radians((357.528+0.9856003*n)%360)
    lam=L+math.radians(1.915)*math.sin(g)+math.radians(0.02)*math.sin(2*g);eps=math.radians(23.439-4e-7*n)
    ra=math.atan2(math.cos(eps)*math.sin(lam),math.cos(lam));dec=math.asin(math.sin(eps)*math.sin(lam))
    gmst=(18.697374558+24.06570982441908*n)%24;H=math.radians(gmst*15+lon)-ra
    el=math.asin(math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(H))
    # azimuth from north clockwise via vector
    x=-math.cos(dec)*math.sin(H);y=math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(H)*math.sin(lat)
    return math.degrees(math.atan2(x,y))%360,math.degrees(el)
if __name__=='__main__':
    for m in range(0,181,15):
        t=datetime.datetime(1992,2,16,2,0)+datetime.timedelta(minutes=m);print(t+datetime.timedelta(hours=10),sunpos(t))
