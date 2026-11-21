# Download Google Images result photos listed in urls.txt ("part host/path" per line). Reference only, never textures.
import sys, os, urllib.request, concurrent.futures as cf
G = sys.argv[1]
L = [l.split(' ', 1) for l in open(G + '/urls.txt').read().split('\n') if l.strip()]
os.makedirs(G + '/img', exist_ok=True)

def get(i):
    p, u = L[i]
    ext = os.path.splitext(u.split(';')[-1])[1][:5] or '.jpg'
    fn = '%s_%03d%s' % (p, i, ext)
    try:
        d = urllib.request.urlopen(urllib.request.Request('https://' + u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0'}), timeout=30).read()
        if len(d) < 8000:
            return None
        open(G + '/img/' + fn, 'wb').write(d)
        return (p, fn + '  https://' + u)
    except Exception:
        return None

with cf.ThreadPoolExecutor(8) as ex:
    R = [r for r in ex.map(get, range(len(L))) if r]
open(G + '/SOURCES.txt', 'w').write('Reference only (Google Images results, 2026-11-21). Never textures.\n' + '\n'.join(r[1] for r in R) + '\n')
c = {}
for p, _ in R:
    c[p] = c.get(p, 0) + 1
print(len(L), len(R), c)
