# WAFL scrape helper: reads a page's __NUXT_DATA__ json (wafl.com.au and footyinfo pages).
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import re,json,sys
def load(path):
    s=open(path,encoding='utf8',errors='replace').read()
    m=re.search(r'<script type="application/json"[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
    arr=json.loads(m.group(1))
    memo={}
    def r(i,depth=0):
        if i in memo: return memo[i]
        v=arr[i]
        if isinstance(v,dict):
            o={}; memo[i]=o
            for k,x in v.items(): o[k]=r(x) if isinstance(x,int) else x
            return o
        if isinstance(v,list):
            if v and isinstance(v[0],str) and v[0] in ('Reactive','ShallowReactive','Ref','ShallowRef','EmptyRef','EmptyShallowRef'):
                return r(v[1]) if len(v)>1 else None
            if v and isinstance(v[0],str) and v[0] in ('Set','Map','Date','RegExp','NuxtError','Error'):
                return v
            o=[]; memo[i]=o
            o.extend(r(x) if isinstance(x,int) else x for x in v); return o
        return v
    return r(0)
if __name__=='__main__':
    d=load(sys.argv[1])
    data=d['data']
    for k,v in data.items():
        print(k, type(v).__name__, (list(v.keys())[:15] if isinstance(v,dict) else len(v) if isinstance(v,list) else v))
