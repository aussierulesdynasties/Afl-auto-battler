# WAFL scrape helper: pulls the HTML tables out of a saved page.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import re,html,sys,json
def tables(path):
    s=open(path,encoding='utf8',errors='replace').read()
    out=[]
    for tb in re.findall(r'<table.*?</table>',s,flags=re.S):
        rows=[]
        for tr in re.findall(r'<tr.*?</tr>',tb,flags=re.S):
            cells=[]
            for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>',tr,flags=re.S):
                href=re.search(r'href="(/player/[^"]+)"',c)
                txt=html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',c))).strip()
                cells.append(txt+('|'+href.group(1) if href else ''))
            rows.append(cells)
        out.append(rows)
    return out
if __name__=='__main__':
    for t in tables(sys.argv[1]):
        print(len(t)); [print(r) for r in t[:4]]
