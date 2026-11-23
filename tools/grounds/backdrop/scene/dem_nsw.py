"""NSW Spatial Services' 5 m elevation (public/NSW_5M_Elevation ImageServer, ground heights from stereo imagery, CC BY 4.0
(c) Spatial Services, DCS NSW) round a ground in NSW: heights only, saved as a lat/lon grid that prep.py samples in
place of the terrarium tiles (spec 'dem_nsw'). Checked at Blacktown 2026-11-23 against 24 Google Earth ground readings
on roads 180-740 m out: median 0.3 m, spread 0.5 m (the terrarium tiles there read up to 10 m high, a surface model
over the trees). usage: dem_nsw.py spec.json"""
import sys, os, json, math, io, urllib.request, urllib.parse
import numpy as np
from PIL import Image
spec = json.load(open(sys.argv[1])); D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', spec['name'])
lat0, lon0 = spec['lat'], spec['lon']; KX = 111320 * math.cos(math.radians(lat0)); KY = 110540
URL = 'https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_5M_Elevation/ImageServer/exportImage'
def grab(half, step, name):
    n = int(round(2 * half / step)) + 1
    b = (lon0 - half / KX, lat0 - half / KY, lon0 + half / KX, lat0 + half / KY)
    q = urllib.parse.urlencode({'bbox': ','.join('%.8f' % v for v in b), 'bboxSR': 4326, 'imageSR': 4326, 'size': '%d,%d' % (n, n),
                                'format': 'tiff', 'pixelType': 'F32', 'interpolation': 'RSP_BilinearInterpolation', 'f': 'image'})
    A = np.asarray(Image.open(io.BytesIO(urllib.request.urlopen(URL + '?' + q, timeout=300).read())), np.float32)
    A = np.where((A < -100) | (A > 3000), np.nan, A)
    np.save(os.path.join(D, name + '.npy'), A); json.dump({'bbox': b, 'n': n}, open(os.path.join(D, name + '.json'), 'w'))
    print(name, A.shape, np.nanmin(A), np.nanmax(A), 'nan', int(np.isnan(A).sum()))
grab(spec['near_half_m'] + 100, 5.0, 'dem_nsw_near')
grab(min(spec['far_half_m'], 30000) + 500, 125.0, 'dem_nsw_far')
