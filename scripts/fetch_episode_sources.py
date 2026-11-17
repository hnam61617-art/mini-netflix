"""Tải metadata TVmaze đã chọn từ các phim bộ có trong log. Không fuzzy-guess show."""
import csv,collections,json,re,unicodedata,time,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return ' '.join(re.sub(r'[^\w\s]',' ',unicodedata.normalize('NFKC',s).casefold()).split())
def main():
 raw=ROOT/'datasets/raw';catalog=list(csv.DictReader((raw/'netflix_titles.csv').open(encoding='utf-8-sig')));shows=[r for r in catalog if r['type']=='TV Show'];counts=collections.Counter()
 for path in [raw/'netflix_watch_log/All_ViewingActivity.csv',raw/'netflix_viewing_activity/ViewingActivity.csv']:
  for row in csv.DictReader(path.open(encoding='utf-8-sig')):
   if row['Supplemental Video Type']:continue
   matches=[r for r in shows if row['Title'].casefold().startswith(r['title'].casefold()+': ')]
   if matches:counts[max(matches,key=lambda r:len(r['title']))['title']]+=1
 directory=raw/'tvmaze';directory.mkdir(exist_ok=True);manifest=[]
 def get(url):
  for attempt in range(3):
   try:
    with urllib.request.urlopen(url,timeout=25) as r:result=json.load(r)
    time.sleep(.6);return result
   except Exception:
    if attempt==2:raise
    time.sleep(2+attempt)
 for title,n in counts.most_common(35):
  key=next(r['show_id'] for r in shows if r['title']==title);path=directory/(key+'.json')
  if path.exists():record=json.loads(path.read_text());manifest.append(record);continue
  url='https://api.tvmaze.com/search/shows?q='+urllib.parse.quote(title)
  try:
   results=get(url);matches=[r['show'] for r in results if norm(r['show']['name'])==norm(title)]
   record=dict(netflix_show_id=key,netflix_title=title,search_url=url,source='TVmaze',license='CC BY-SA 4.0')
   if len(matches)!=1:record.update(status='unresolved',reason='exact_name_candidates='+str(len(matches)))
   else:
    show=matches[0];epsurl='https://api.tvmaze.com/shows/'+str(show['id'])+'/episodes';episodes=get(epsurl)
    record.update(status='matched_exact_title',show=show,episodes_url=epsurl,episodes=episodes)
   path.write_text(json.dumps(record,ensure_ascii=False,indent=2));manifest.append(record);print(title,record['status'],len(record.get('episodes',[])),flush=True)
  except Exception as e:
   record=dict(netflix_show_id=key,netflix_title=title,status='download_failed',reason=str(e)[:160]);path.write_text(json.dumps(record,ensure_ascii=False));manifest.append(record);print(title,'FAILED',flush=True)
 (ROOT/'datasets/metadata/tvmaze_fetch_manifest.json').write_text(json.dumps([{k:v for k,v in r.items() if k not in ['show','episodes']} for r in manifest],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
