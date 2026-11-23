"""Download Commons files (1600 px thumbs) as reference only; records title, author, licence, url in refs.json.
get_commons.py out_dir "File:..." ..."""
import sys, os, json, urllib.request, urllib.parse
out = sys.argv[1]; titles = sys.argv[2:]
UA = {'User-Agent': 'StadiumSceneReference/0.2 (one-off reference download, about 10 files, low rate) Python-urllib/3.14'}
q = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({'action': 'query', 'titles': '|'.join(titles), 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 1280, 'format': 'json'})
d = json.loads(urllib.request.urlopen(urllib.request.Request(q, headers=UA), timeout=60).read())
refp = os.path.join(out, 'refs.json'); refs = json.load(open(refp)) if os.path.exists(refp) else {}
for p in d['query']['pages'].values():
    if 'imageinfo' not in p: print('missing', p.get('title')); continue
    ii = p['imageinfo'][0]; md = ii.get('extmetadata', {})
    fn = ''.join(c if c.isalnum() or c in '._-' else '_' for c in p['title'][5:])
    fn = os.path.splitext(fn)[0] + '.jpg'
    open(os.path.join(out, fn), 'wb').write(urllib.request.urlopen(urllib.request.Request(ii['url'], headers=UA), timeout=120).read())
    refs[fn] = {'title': p['title'], 'page': ii['descriptionurl'], 'author': md.get('Artist', {}).get('value', '')[:120], 'licence': md.get('LicenseShortName', {}).get('value', ''), 'date': md.get('DateTimeOriginal', {}).get('value', '')[:40]}
    print(fn, refs[fn]['licence'])
json.dump(refs, open(refp, 'w'), indent=1)
