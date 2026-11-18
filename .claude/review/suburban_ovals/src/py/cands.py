import json,sys,time,os,urllib.parse,subprocess
from PIL import Image,ImageDraw
OUT=sys.argv[1]; cats=sys.argv[2:]
UA="groundref/0.1"
def api(params):
    q=urllib.parse.urlencode(params)
    r=subprocess.run(["curl","-s","-A",UA,"https://commons.wikimedia.org/w/api.php?"+q],capture_output=True)
    return json.loads(r.stdout)
for c in cats:
    try: d=api(dict(action="query",generator="categorymembers",gcmtitle="Category:"+c,gcmtype="file",gcmlimit=40,prop="imageinfo",iiprop="url|size|timestamp",iiurlwidth=320,format="json"))
    except Exception as e: print("api fail",c,e); time.sleep(5); continue
    pages=list(d.get("query",{}).get("pages",{}).values())
    tiles=[];meta=[]
    for p in pages:
        i=p["imageinfo"][0]
        if i["width"]<1200: continue
        fn=os.path.join(OUT,"t_%s.jpg"%(__import__("hashlib").md5(p["title"].encode()).hexdigest()[:10]))
        if not os.path.exists(fn):
            subprocess.run(["curl","-s","-A",UA,"-o",fn,i["thumburl"]]); time.sleep(0.7)
        try: im=Image.open(fn).convert("RGB")
        except Exception: continue
        im.thumbnail((320,240)); tiles.append(im); meta.append((p["title"],i["width"],i["height"],i["url"]))
    if not tiles: print("none",c); continue
    n=len(tiles); cols=5; rows=(n+cols-1)//cols
    sheet=Image.new("RGB",(cols*320,rows*260),"white"); dr=ImageDraw.Draw(sheet)
    for k,(im,m) in enumerate(zip(tiles,meta)):
        x,y=(k%cols)*320,(k//cols)*260; sheet.paste(im,(x,y)); dr.text((x+3,y+242),"%d %s"%(k,m[0][5:40]),fill="black")
    safe=c.replace(" ","_").replace(",","")
    sheet.save(os.path.join(OUT,"sheet_%s.jpg"%safe),quality=80)
    json.dump(meta,open(os.path.join(OUT,"meta_%s.json"%safe),"w"),indent=0)
    print(c,n)
