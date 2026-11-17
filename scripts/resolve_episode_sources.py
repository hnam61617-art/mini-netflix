"""Giải quyết tên phim trùng bằng diễn viên nguồn hoặc alias tên gốc; giữ bằng chứng."""
import json,csv,urllib.request,urllib.parse,time,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def norm(v):return ' '.join(re.sub(r'[^\w\s]',' ',unicodedata.normalize('NFKC',v).casefold()).split())
def get(url):
 with urllib.request.urlopen(url,timeout=25) as r:v=json.load(r)
 time.sleep(.6);return v
for path in (ROOT/'datasets/raw/tvmaze').glob('*.json'):
 record=json.loads(path.read_text())
 if record.get('status')!='unresolved':continue
 raw=next(r for r in csv.DictReader((ROOT/'datasets/raw/netflix_titles.csv').open(encoding='utf-8-sig')) if r['show_id']==record['netflix_show_id'])
 if raw['title'] not in ['Friends','Suits','Demon Slayer: Kimetsu no Yaiba']:continue
 try:
  query=raw['title'].split(': ',1)[-1] if raw['title'].startswith('Demon Slayer:') else raw['title']
  results=get('https://api.tvmaze.com/search/shows?q='+urllib.parse.quote(query));sourcecast={norm(v) for v in raw['cast'].split(',')}
  evidence=[];matches=[]
  for result in results[:5]:
   show=result['show']
   if norm(show['name'])!=norm(raw['title']) and not norm(raw['title']).endswith(norm(show['name'])):continue
   cast=get('https://api.tvmaze.com/shows/'+str(show['id'])+'/cast');overlap=sourcecast&{norm(x['person']['name']) for x in cast}
   evidence.append(dict(show_id=show['id'],show_name=show['name'],cast_overlap=sorted(overlap)))
   if len(overlap)>=2:matches.append(show)
   elif raw['title'].startswith('Demon Slayer:') and show.get('premiered','')[:4]==raw['release_year'] and norm(raw['title']).endswith(norm(show['name'])):matches.append(show)
  record['resolution_evidence']=evidence
  if len(matches)==1:
   show=matches[0];url='https://api.tvmaze.com/shows/'+str(show['id'])+'/episodes';record.update(status='matched_title_and_cast_or_original_name',show=show,episodes_url=url,episodes=get(url),resolution='unique >=2 cast intersection, or original-name suffix + exact premiere year for Demon Slayer')
  path.write_text(json.dumps(record,ensure_ascii=False,indent=2));print(raw['title'],record['status'],len(record.get('episodes',[])),flush=True)
 except Exception as e:print(raw['title'],type(e).__name__,str(e)[:100],flush=True)
