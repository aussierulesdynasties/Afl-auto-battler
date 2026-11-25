"""Parse AFL Tables' season pages (afltables.com/afl/seas/<year>.html, saved as s<year>.html in
the folder given) into data/raw/attendance_2023_2026.csv: every match's round, clubs, start time
on the ground's own clock, ground and crowd. Usage: python3 parse_afltables.py DIR > out.csv"""
import re,sys,csv,html
rows=[]
for y in (2023,2024,2025,2026):
    s=open(f"{sys.argv[1]}/s{y}.html",encoding='latin-1').read()
    # split by round header tables and game tables in order
    tokens=re.finditer(r'<b>(Round \d+|Qualifying Final|Elimination Final|Semi Final|Preliminary Final|Grand Final|Opening Round)|<tr[^>]*><td width=16%><a href="[^"]*">([^<]+)</a></td><td[^>]*><tt>[^<]*</tt></td><td[^>]*>\s*(\d+)</td><td>([^<]*)(?:<b>Att: </b>([\d,]+))?\s*(?:<b>Venue:</b> <a[^>]*>([^<]+)</a>)?',s)
    rnd=None;cur=None
    for m in tokens:
        if m.group(1):
            rnd=m.group(1);continue
        team=html.unescape(m.group(2));info=m.group(4) or ''
        if m.group(6):
            cur=dict(year=y,round=rnd,home=team,when=info.strip(),att=(m.group(5) or '').replace(',',''),venue=html.unescape(m.group(6)))
        elif cur:
            cur['away']=team;rows.append(cur);cur=None
w=csv.DictWriter(sys.stdout,fieldnames=['year','round','home','away','when','venue','att'])
w.writeheader();[w.writerow(r) for r in rows]
