import json,urllib.request,urllib.parse,os
T=["TIO Stadium, Darwin, September 2025 %02d.jpg"%i for i in range(1,22)]+["AFL Northern Territory office at TIO Stadium, September 2025.jpg","Marrara Oval grandstand.png","Marrara Stadium (1).jpg","Marrara Stadium.jpg","TIO Stadium.jpg"]
H={'User-Agent':'afl-ground-builder/1.0'}
meta={}
for i in range(0,len(T),20):
    q='|'.join('File:'+t for t in T[i:i+20])
    u='https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=2000&format=json&titles='+urllib.parse.quote(q)
    d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H)))
    for p in d['query']['pages'].values():
        ii=p['imageinfo'][0];em=ii['extmetadata']
        meta[p['title']]={'url':ii.get('thumburl',ii['url']),'w':ii['width'],'h':ii['height'],'lic':em.get('LicenseShortName',{}).get('value'),'date':em.get('DateTimeOriginal',{}).get('value','')[:40],'artist':em.get('Artist',{}).get('value','')[:80]}
json.dump(meta,open("refs/meta.json","w"),indent=1)
for k,(t,m) in enumerate(sorted(meta.items())):
    fn='refs/'+t[5:].replace(' ','_').replace(',','')
    fn=os.path.splitext(fn)[0]+'.jpg'
    import time
    for a in range(6):
      if os.path.exists(fn):break
      try:open(fn,"wb").write(urllib.request.urlopen(urllib.request.Request(m["url"],headers=H)).read())
      except Exception as e:
        if os.path.exists(fn):os.remove(fn)
        time.sleep(6*(a+1))
    time.sleep(2)
    if 0:
        open(fn,'wb').write(urllib.request.urlopen(urllib.request.Request(m['url'],headers=H)).read())
    print(fn,m['w'],m['h'],m['lic'],m['date'])
json.dump(meta,open('refs/meta.json','w'),indent=1)
