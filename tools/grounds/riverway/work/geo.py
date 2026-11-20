import math
# Riverway Stadium origin: provisional (OSM stadium way 175599089 centroid); replaced by the fence-ellipse centre once traced
LAT0,LON0=-19.317618,146.731873
p=math.radians(LAT0)
MLAT=111132.92-559.82*math.cos(2*p)+1.175*math.cos(4*p)
MLON=111412.84*math.cos(p)-93.5*math.cos(3*p)
def ll2xy(lat,lon): return ((lon-LON0)*MLON,(lat-LAT0)*MLAT)
def xy2ll(x,y): return (LAT0+y/MLAT,LON0+x/MLON)
