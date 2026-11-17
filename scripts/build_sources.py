"""Rebuild ngoại tuyến: nguồn có provenance, không tạo payment/watchlist/lịch sử ngẫu nhiên."""
import csv,json,re,hashlib,unicodedata,sys
from datetime import datetime,date,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'datasets/raw';OUT=ROOT/'datasets/generated'
NAMES=['Nguyễn Minh Khôi','Trần Ngọc Anh','Lê Quang Huy','Phạm Thu Hà','Hoàng Đức Anh','Huỳnh Gia Hân','Phan Anh Tuấn','Vũ Bảo Ngọc','Võ Hải Nam','Đặng Phương Linh','Bùi Tuấn Kiệt','Đỗ Minh Châu','Hồ Thanh Tùng']
CANONICAL={'Action & Adventure':1,'TV Action & Adventure':1,'Comedies':2,'TV Comedies':2,'Stand-Up Comedy':2,'Stand-Up Comedy & Talk Shows':2,'Dramas':3,'TV Dramas':3,'Sci-Fi & Fantasy':4,'TV Sci-Fi & Fantasy':4}
def clean(v):return ' '.join(unicodedata.normalize('NFC',v or '').split())
def norm(v):return ' '.join(re.sub(r'[^\w\s]',' ',unicodedata.normalize('NFKC',v or '').casefold()).split())
def quote(v):
 if v is None:return 'NULL'
 if isinstance(v,(int,float)):return str(v)
 return "'"+str(v).replace('\\','\\\\').replace("'","''")+"'"
def insert(table,cols,rows):
 rows=list(rows);out=[]
 for i in range(0,len(rows),200):out.append('INSERT INTO '+table+' ('+','.join(cols)+') VALUES\n'+',\n'.join('('+', '.join(quote(v) for v in r)+')' for r in rows[i:i+200])+';')
 return '\n\n'.join(out)
def csvwrite(name,rows,fields=None):
 rows=list(rows)
 with (OUT/name).open('w',encoding='utf-8',newline='') as f:
  if fields is None:fields=list(rows[0]) if rows else ['reason']
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def seconds(value):
 if not re.fullmatch(r'\d+:\d{2}:\d{2}',value or ''):return None
 h,m,s=map(int,value.split(':'))
 return h*3600+m*60+s if m<60 and s<60 else None
def main():
 OUT.mkdir(exist_ok=True);csvpath=RAW/'netflix_titles.csv'
 locked=ROOT/'datasets/metadata/raw_sha256.json'
 current_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAW.rglob('*')) if p.is_file()}
 if locked.exists() and '--refresh-snapshot' not in sys.argv and json.loads(locked.read_text())!=current_hashes:raise ValueError('Raw snapshot đã đổi. Kiểm tra nguồn trước khi dùng --refresh-snapshot.')
 if hashlib.sha256(csvpath.read_bytes()).hexdigest()!='df1f4ad2027a5a14c3a33932ef0d4054565ff88adf92b7f263601b70fdc6f3f3':raise ValueError('Snapshot CSV thay đổi')
 records=list(csv.DictReader(csvpath.open(encoding='utf-8-sig')));movies=[r for r in records if r['type']=='Movie'];shows=[r for r in records if r['type']=='TV Show']
 anchor=next(r for r in movies if r['show_id']=='s142');empty=next(r for r in shows if r['show_id']=='s4')
 first=[anchor]+[r for r in movies if r is not anchor][:49]+[r for r in shows if r is not empty][:29]+[empty];used={r['show_id'] for r in first};ordered=first+[r for r in records if r['show_id'] not in used]
 ids={r['show_id']:i for i,r in enumerate(ordered,1)};source_by_id={ids[r['show_id']]:r for r in ordered}
 tags=sorted({clean(v) for r in records for v in r['listed_in'].split(',')});gids={v:i+5 for i,v in enumerate(tags)}
 genres=[(1,'Hành động'),(2,'Hài'),(3,'Tâm lý'),(4,'Khoa học viễn tưởng')]+[(gids[v],v) for v in tags]
 episode_rows=[];episode_map=[];episode_skips=[];show_evidence={};show_dates={};episode_lookup={}
 for path in sorted((RAW/'tvmaze').glob('*.json'),key=lambda p:ids.get(p.stem,999999)):
  bundle=json.loads(path.read_text());key=bundle['netflix_show_id'];cid=ids[key]
  if not bundle.get('status','').startswith('matched_'):continue
  show_evidence[cid]=bundle;premiered=bundle['show'].get('premiered');show_dates[cid]=premiered if premiered and re.fullmatch(r'\d{4}-\d{2}-\d{2}',premiered) else None
  eps=sorted(bundle['episodes'],key=lambda e:(e.get('season') or 0,e.get('number') or 0,e['id']))
  for ep in eps:
   reason=None
   if not ep.get('name'):reason='episode_name_missing'
   elif not isinstance(ep.get('runtime'),int) or ep['runtime']<=0:reason='runtime_missing_NOT_NULL'
   elif not isinstance(ep.get('season'),int) or not isinstance(ep.get('number'),int):reason='non_regular_episode_number'
   elif ep.get('airdate') and ep['airdate']>'2026-11-16':reason='future_episode_at_snapshot'
   title=f"S{ep.get('season',0):02d}E{ep.get('number',0):02d} · {clean(ep.get('name',''))}" if isinstance(ep.get('season'),int) and isinstance(ep.get('number'),int) else ''
   if len(title)>255:reason='title_over_255'
   if reason:episode_skips.append(dict(content_id=cid,source_episode_id=ep['id'],reason=reason));continue
   eid=len(episode_rows)+1;position=1+sum(1 for r in episode_rows if r[1]==cid)
   episode_rows.append((eid,cid,position,title,ep['runtime'],'https://example.com/no-video/tvmaze-'+str(ep['id']),ep.get('airdate') or None))
   evidence=dict(episode_id=eid,content_id=cid,tvmaze_show_id=bundle['show']['id'],tvmaze_episode_id=ep['id'],source_season=ep['season'],source_number=ep['number'],source_name=ep['name'],runtime_minutes=ep['runtime'],airdate=ep.get('airdate') or '',source_url=ep['url'],license='CC BY-SA 4.0')
   episode_map.append(evidence);episode_lookup.setdefault(cid,[]).append((ep,eid))
 content_rows=[];movie_rows=[];series_rows=[];links=[];catalogmap=[];runtime_map={};title_map={}
 for cid,r in enumerate(ordered,1):
  kind='MOVIE' if r['type']=='Movie' else 'TV_SERIES';title=clean(r['title']);exact_date=show_dates.get(cid)
  content_rows.append((cid,title,clean(r['description']),exact_date,kind));title_map.setdefault(norm(title),[]).append(cid)
  row_gids=set()
  for tag in map(clean,r['listed_in'].split(',')):
   row_gids.add(gids[tag])
   if tag in CANONICAL:row_gids.add(CANONICAL[tag])
  links.extend((cid,gid) for gid in sorted(row_gids))
  if kind=='MOVIE':
   duration=r['duration'] or r['rating'];match=re.fullmatch(r'(\d+) min',duration)
   if not match or int(match[1])<=0:raise ValueError('Movie runtime missing '+r['show_id'])
   runtime_map[cid]=int(match[1]);movie_rows.append((cid,'https://example.com/no-video/'+r['show_id'],int(match[1])))
  else:series_rows.append((cid,))
  catalogmap.append(dict(content_id=cid,show_id=r['show_id'],source_title=r['title'],content_type=kind,release_year=r['release_year'],date_released=exact_date or '',date_source='TVmaze premiered' if exact_date else 'missing_exact_date_NULL',source_duration=r['duration'],duration_recovered_from_rating=not bool(r['duration']) and kind=='MOVIE',source_listed_in=r['listed_in']))
 # One technical owner per source-profile namespace. No claim of identifying the real account holder.
 arjun_profiles=list(csv.DictReader((RAW/'netflix_watch_log/All_Profiles.csv').open(encoding='utf-8-sig')));original_profile_rows={p['Profile Name']:i+2 for i,p in enumerate(arjun_profiles)};arjun_profiles.sort(key=lambda r:(r['Profile Name']!='User 4',r['Profile Name']))
 streams=[('netflix_watch_log',RAW/'netflix_watch_log/All_ViewingActivity.csv'),('netflix_viewing_activity',RAW/'netflix_viewing_activity/ViewingActivity.csv')]
 source_rows={key:list(csv.DictReader(path.open(encoding='utf-8-sig'))) for key,path in streams}
 profile_records=[('netflix_watch_log',p['Profile Name'],datetime.strptime(p['Profile Creation Time'],'%d-%m-%Y %H:%M'), 'All_Profiles.csv',original_profile_rows[p['Profile Name']]) for i,p in enumerate(arjun_profiles)]
 for alias in sorted({r['Profile Name'] for r in source_rows['netflix_viewing_activity']}):
  times=[datetime.fromisoformat(r['Start Time']) for r in source_rows['netflix_viewing_activity'] if r['Profile Name']==alias]
  profile_records.append(('netflix_viewing_activity',alias,min(times),'derived_from_first_observed_log',0))
 password_hash=json.loads((ROOT/'datasets/metadata/demo_config.json').read_text())['password_hash']
 users=[];profiles=[];profile_map=[];profile_ids={};created_times={}
 for i,(source,alias,created,origin,rowno) in enumerate(profile_records,1):
  fullname=NAMES[i-1];when=created.strftime('%Y-%m-%d %H:%M:%S')
  users.append((i,f'student{i:03d}@gmail.com',f'09{i:08d}',password_hash,fullname,when));profiles.append((i,i,' '.join(fullname.split()[1:]),when));profile_ids[(source,alias)]=i;created_times[i]=created
  profile_map.append(dict(user_id=i,profile_id=i,source=source,source_profile_alias=alias,display_alias=' '.join(fullname.split()[1:]),owner_identity='technical_placeholder_not_source_identity',created_at=when,created_at_source=origin,source_row=rowno))
 # Import only matched main-feature events with a known runtime and actual bookmark.
 all_events=[];rejected=[];all_show_titles=sorted([(norm(r['title']),cid) for cid,r in source_by_id.items() if r['type']=='TV Show'],key=lambda t:len(t[0]),reverse=True)
 def resolve(title):
  direct=title_map.get(norm(title),[])
  if len(direct)==1 and source_by_id[direct[0]]['type']=='Movie':return ('MOVIE',direct[0],runtime_map[direct[0]])
  # Netflix labels separate the exact series title with ': '. No fuzzy title matching.
  candidates=[cid for cid,r in source_by_id.items() if r['type']=='TV Show' and title.casefold().startswith(r['title'].casefold()+': ')]
  if not candidates:return None
  cid=max(candidates,key=lambda c:len(source_by_id[c]['title']));rest=title[len(source_by_id[cid]['title'])+2:]
  season_match=re.search(r'\bSeason (\d+)\b',rest,re.I);season=int(season_match[1]) if season_match else None
  parts=rest.split(': ',1);episode_title=parts[1] if len(parts)>1 else rest
  episode_title=re.sub(r'\s*\(Episode \d+\)\s*$','',episode_title,flags=re.I).strip()
  generic=re.fullmatch(r'Episode (\d+)',episode_title,re.I)
  matches=[]
  for ep,eid in episode_lookup.get(cid,[]):
   if season is not None and ep['season']!=season:continue
   # Name match is required; numeric episode labels accepted only if source itself uses them.
   if norm(ep['name'])==norm(episode_title):matches.append((eid,ep['runtime']))
  if len(matches)==1:return ('EPISODE',matches[0][0],matches[0][1])
  return None
 for source,rows in source_rows.items():
  for rowno,row in enumerate(rows,2):
   reason=None;pid=profile_ids[(source,row['Profile Name'])]
   if row['Supplemental Video Type']:reason='supplemental_'+row['Supplemental Video Type'].lower()
   duration=seconds(row['Duration']);bookmark=seconds(row['Bookmark']);target=None
   if not reason and (duration is None or duration<=0):reason='zero_or_invalid_watch_duration'
   if not reason:
    target=resolve(row['Title'])
    if not target:reason='unmatched_or_ambiguous_title_episode_or_runtime'
   if not reason and bookmark is None:reason='bookmark_missing_progress_NOT_NULL'
   try:start=datetime.fromisoformat(row['Start Time'])
   except ValueError:start=None;reason='invalid_start_time'
   if not reason and start<created_times[pid]:reason='event_precedes_profile_creation'
   if reason:rejected.append(dict(source=source,row=rowno,title=row['Title'],reason=reason));continue
   kind,key,runtime=target;raw_progress=100*bookmark/(runtime*60);progress=round(min(100,max(0,raw_progress)),2);end=start+timedelta(seconds=duration)
   all_events.append(dict(source=source,row=rowno,profile_id=pid,kind=kind,target_id=key,start_time=row['Start Time'],duration_seconds=duration,bookmark_seconds=bookmark,runtime_minutes=runtime,raw_percent=round(raw_progress,6),watch_progress=progress,last_watch_at=end.strftime('%Y-%m-%d %H:%M:%S'),clamped=raw_progress>100,title=row['Title']))
 # Unique constraints require one latest observation per profile/target, not all repeated plays.
 latest={}
 for event in all_events:
  key=(event['profile_id'],event['kind'],event['target_id'])
  if key not in latest or (event['last_watch_at'],event['row'])>(latest[key]['last_watch_at'],latest[key]['row']):latest[key]=event
 histories=[];history_map=[]
 for hid,((pid,kind,key),event) in enumerate(sorted(latest.items()),1):
  histories.append((hid,pid,key if kind=='MOVIE' else None,key if kind=='EPISODE' else None,event['watch_progress'],event['last_watch_at']));history_map.append(dict(history_id=hid,**event))
 tiers=[(1,'Cơ bản',70000,2,1,'SD'),(2,'Tiêu chuẩn',120000,4,2,'HD'),(3,'Cao cấp',180000,5,4,'4K')]
 # Plan configuration is demo application configuration, not imported subscription transactions.
 chunks=['SET NAMES utf8mb4;','USE mini_netflix;','START TRANSACTION;',insert('users',['user_id','email','phone','password_hash','full_name','created_at'],users),insert('profiles',['profile_id','user_id','profile_name','created_at'],profiles),insert('subscription_tiers',['tier_id','tier_name','prices','max_profile','max_device','video_quality'],tiers),insert('genres',['genre_id','genre_name'],genres),insert('contents',['content_id','title','description','date_released','content_type'],content_rows),insert('movies',['content_id','video_url','duration'],movie_rows),insert('tv_series',['content_id'],series_rows),insert('episodes',['episode_id','content_id','episode_number','title','duration','video_url','date_released'],episode_rows),insert('content_genres',['content_id','genre_id'],links),insert('watch_histories',['history_id','profile_id','content_id','episode_id','watch_progress','last_watch_at'],histories),'COMMIT;']
 (ROOT/'sql/02_seed.sql').write_text('\n\n'.join(x for x in chunks if x)+'\n')
 csvwrite('content_provenance.csv',catalogmap);csvwrite('episode_provenance.csv',episode_map);csvwrite('profile_provenance.csv',profile_map);csvwrite('history_provenance.csv',history_map);csvwrite('rejected_watch_events.csv',rejected);csvwrite('rejected_episodes.csv',episode_skips)
 counts=dict(users=len(users),profiles=len(profiles),subscription_tiers=3,subscriptions=0,payments=0,contents=len(content_rows),movies=len(movie_rows),tv_series=len(series_rows),episodes=len(episode_rows),genres=len(genres),content_genres=len(links),watch_lists=0,watch_histories=len(histories))
 summary=dict(table_counts=counts,total_rows=sum(counts.values()),source_catalog_rows=8807,source_watch_rows=sum(len(v) for v in source_rows.values()),matched_events_before_latest=len(all_events),latest_histories=len(histories),repeated_matched_events_collapsed=len(all_events)-len(histories),rejected_watch_events=len(rejected),rejected_reasons=dict(__import__('collections').Counter(r['reason'] for r in rejected)),imported_series_with_episodes=len({r[1] for r in episode_rows}),date_released_nulls=sum(r[3] is None for r in content_rows),technical_accounts=len(users),empty_tables=['subscriptions','payments','watch_lists'],report_sha256=hashlib.sha256((ROOT/'docs/bao_cao_do_an.docx').read_bytes()).hexdigest())
 (OUT/'build_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
 source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAW.rglob('*')) if p.is_file()};(ROOT/'datasets/metadata/raw_sha256.json').write_text(json.dumps(source_hashes,indent=2))
if __name__=='__main__':main()
