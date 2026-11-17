"""Kiểm chứng bộ nguồn chính. --fresh kiểm số dòng ban đầu và ba bảng để trống."""
import os,sys,json,csv,hashlib,re,unicodedata
from pathlib import Path
from datetime import datetime,timedelta
from decimal import Decimal
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'demo'))
import app
from verify import conn,statements

def main():
 out=[];c=conn();m=json.loads((ROOT/'datasets/generated/build_manifest.json').read_text());fresh='--fresh' in sys.argv
 def check(code,name,ok,actual):out.append(dict(code=code,name=name,passed=bool(ok),actual=str(actual)))
 def scalar(sql,args=()):
  with c.cursor() as q:q.execute(sql,args);return q.fetchone()[0]
 checks=json.loads((ROOT/'datasets/metadata/preserved_files_sha256.json').read_text())
 check('S01','Báo cáo, schema, role, SELECT và bốn verify gốc giữ nguyên byte',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in checks.items()),len(checks))
 hashes=json.loads((ROOT/'datasets/metadata/raw_sha256.json').read_text());check('S02','Tất cả snapshot nguồn khớp SHA-256',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in hashes.items()),len(hashes))
 check('S03','13 bảng nghiệp vụ',scalar("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='mini_netflix' AND table_type='BASE TABLE'")==13,13)
 check('S04','13 trigger',scalar("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='mini_netflix'")==13,13)
 check('S05','4 view',scalar("SELECT COUNT(*) FROM information_schema.views WHERE table_schema='mini_netflix'")==4,4)
 check('S06','Một thủ tục',scalar("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='mini_netflix'")==1,1)
 for table,n in m['table_counts'].items():
  actual=scalar('SELECT COUNT(*) FROM '+table)
  if fresh:check('COUNT-'+table,'Số dòng seed '+table,actual==n,f'{actual}/{n}')
 check('S07','Bộ chính vượt 20000 dòng không sinh log ngẫu nhiên',sum(m['table_counts'].values())>=20000,m['total_rows'])
 check('S08','Bộ chính không INSERT ba bảng thiếu nguồn',not any(('INSERT INTO '+t) in (ROOT/'sql/02_seed.sql').read_text() for t in ['subscriptions','payments','watch_lists']),m['empty_tables'])
 check('S09','Không tạo tập giả',scalar("SELECT COUNT(*) FROM episodes WHERE title LIKE 'Tập mô phỏng%%'")==0,'0')
 check('S10','Mọi bộ đếm tập khớp dòng đã nhập',scalar('SELECT COUNT(*) FROM tv_series s LEFT JOIN (SELECT content_id,COUNT(*) n FROM episodes GROUP BY content_id) e ON e.content_id=s.content_id WHERE s.total_episodes<>COALESCE(e.n,0)')==0,'0 violations')
 check('S11','Đúng lớp con + ít nhất một thể loại',scalar("SELECT COUNT(*) FROM contents c LEFT JOIN movies mo ON mo.content_id=c.content_id LEFT JOIN tv_series s ON s.content_id=c.content_id WHERE (mo.content_id IS NOT NULL)+(s.content_id IS NOT NULL)<>1 OR NOT EXISTS (SELECT 1 FROM content_genres cg WHERE cg.content_id=c.content_id)")==0,'0 violations')
 profilemap=list(csv.DictReader((ROOT/'datasets/generated/profile_provenance.csv').open()));historymap=list(csv.DictReader((ROOT/'datasets/generated/history_provenance.csv').open()));episodemap=list(csv.DictReader((ROOT/'datasets/generated/episode_provenance.csv').open()))
 check('S12','Mỗi hồ sơ nguồn có chủ kỹ thuật riêng, không giả làm danh tính gốc',len(profilemap)==13 and len({p['profile_id'] for p in profilemap})==13 and all(p['owner_identity']=='technical_placeholder_not_source_identity' for p in profilemap),13)
 rawprofiles=list(csv.DictReader((ROOT/'datasets/raw/netflix_watch_log/All_Profiles.csv').open(encoding='utf-8-sig')))
 check('S13','Dòng hồ sơ nguồn được đối chiếu chính xác sau đổi alias',all(rawprofiles[int(p['source_row'])-2]['Profile Name']==p['source_profile_alias'] for p in profilemap if p['source']=='netflix_watch_log'),'source row verified')
 streams={'netflix_watch_log':list(csv.DictReader((ROOT/'datasets/raw/netflix_watch_log/All_ViewingActivity.csv').open(encoding='utf-8-sig'))),'netflix_viewing_activity':list(csv.DictReader((ROOT/'datasets/raw/netflix_viewing_activity/ViewingActivity.csv').open(encoding='utf-8-sig')))}
 check('S14','905 dòng viewing activity không bị nhân đôi',len(streams['netflix_viewing_activity'])==905,len(streams['netflix_viewing_activity']))
 with c.cursor() as q:
  q.execute('SELECT history_id,profile_id,content_id,episode_id,watch_progress,last_watch_at FROM watch_histories');dbhist={x[0]:x for x in q.fetchall()}
  q.execute('SELECT episode_id,content_id,title,duration,date_released FROM episodes');dbeps={x[0]:x for x in q.fetchall()}
 ok=True;original=True;timing=True
 for row in historymap:
  h=dbhist.get(int(row['history_id']));source=streams[row['source']][int(row['row'])-2]
  original &= source['Title']==row['title'] and not source['Supplemental Video Type']
  target=int(row['target_id']);cid=target if row['kind']=='MOVIE' else None;eid=target if row['kind']=='EPISODE' else None
  percent=round(min(100,max(0,int(row['bookmark_seconds'])*100/(int(row['runtime_minutes'])*60))),2)
  ok &= bool(h) and h[1:5]==(int(row['profile_id']),cid,eid,Decimal(str(percent)))
  end=datetime.fromisoformat(source['Start Time'])+timedelta(seconds=int(row['duration_seconds']));timing &= bool(h) and h[5]==end
 check('S15','Mọi lịch sử có dòng nguồn thật, không phải trailer',original,len(historymap))
 check('S16','Tiến độ từ bookmark/runtime, FK đích đúng và 0..100',ok,len(historymap))
 check('S17','last_watch_at giữ thời điểm kết thúc từ log gốc',timing,len(historymap))
 check('S18','Số log đầu vào được giải thích hết: nhận + loại',m['source_watch_rows']==m['matched_events_before_latest']+m['rejected_watch_events'],m['source_watch_rows'])
 check('S19','Unique profile/target được gộp quan sát cuối',len(historymap)==m['latest_histories'] and m['matched_events_before_latest']-len(historymap)==m['repeated_matched_events_collapsed'],m['latest_histories'])
 episode_ok=True
 for row in episodemap:
  entry=dbeps.get(int(row['episode_id']));episode_ok &= bool(entry) and entry[1]==int(row['content_id']) and entry[3]==int(row['runtime_minutes']) and (str(entry[4]) if entry[4] else '')==row['airdate'] and unicodedata.normalize('NFC',row['source_name']) in unicodedata.normalize('NFC',entry[2])
 check('S20','Tất cả tập có ID, tên, runtime, ngày từ TVmaze',episode_ok and len(episodemap)==m['table_counts']['episodes'],len(episodemap))
 check('S21','Không gán ngày 01/01 khi nguồn chỉ có năm',scalar('SELECT COUNT(*) FROM contents WHERE date_released IS NULL')==m['date_released_nulls'],m['date_released_nulls'])
 check('S22','Không lẫn fixture 25000 log vào seed nguồn',m['table_counts']['watch_histories']<25000 and 'verification_seed' not in (ROOT/'scripts/init_db.py').read_text(),'fixture separated')
 check('S23','File MD dữ liệu để trống và nguồn có sẵn',all((ROOT/n).exists() for n in ['DATA_SOURCES.md','DU_LIEU_CON_TRONG.md','SOURCE_INVENTORY.md']),True)
 queries=json.loads((ROOT/'queries.json').read_text())
 with c.cursor() as q:
  q.execute('SET @profile_id=1')
  for i,(title,text) in enumerate(queries,1):
   for sql in statements(text):q.execute(sql)
   rows=q.fetchall();check('SELECT'+str(i),'SELECT gốc '+str(i)+' chạy được trên bộ thiếu dữ liệu',True,len(rows))
 olduser=os.getenv('DB_USER');oldpass=os.environ['DB_PASSWORD'];os.environ.update(DB_USER='mn_service',DB_PASSWORD='DemoViewer1313!',LAB_ENABLED='1',LAB_KEY='G2Demo1313!')
 try:
  client=app.app.test_client();client.get('/login')
  def post(path,**kw):
   with client.session_transaction() as s:token=s['csrf']
   return client.post(path,data=dict(csrf=token,**kw))
  r=post('/login',email='student001@gmail.com',password='MiniNetflix1313!');check('HTTP-LOGIN','Tài khoản kỹ thuật đăng nhập',r.status_code==302,r.status_code)
  for i,path in enumerate(['/','/?page=2','/?page=184','/?view=list','/?view=history','/account','/content/1','/data-sources']):
   r=client.get(path);check('HTTP'+str(i),'HTTP '+path,r.status_code==200,r.status_code)
  r=client.get('/account');check('HTTP-NOPLAN','Gói trống được hiển thị đúng',b'Ch' in r.data and 'Chưa có gói'.encode() in r.data,r.status_code)
  r=post('/progress',profile_id=1,target='movie:1',watch_progress=90);check('HTTP-BLOCK','Không có gói thì không ghi tiến độ',r.status_code==403,r.status_code)
  r=client.get('/?profile_id=2');check('HTTP-OWNER','Không đọc hồ sơ của chủ khác',r.status_code==403,r.status_code)
  post('/lab/login',key='G2Demo1313!')
  cases=[dict(task='users',user_id=1,run=1),dict(task='profiles',user_id=1,run=1),dict(task='contents',term='Extraction',run=1),dict(task='monthly',date_from='2025-01-01',date_to='2025-12-31',run=1),dict(task='tier_revenue',date_from='2025-01-01',date_to='2025-12-31',run=1),dict(task='pending_list',profile_id=1,run=1),dict(task='series_progress',profile_id=1,run=1)]
  for i,params in enumerate(cases):
   r=client.get('/lab/search',query_string=params);check('SEARCH'+str(i),'Tra cứu '+params['task'],r.status_code==200,r.status_code)
  with c.cursor() as q:q.execute('SELECT DISTINCT content_id FROM episodes ORDER BY content_id LIMIT 1');cid=q.fetchone()[0]
  r=client.get('/content/'+str(cid));check('HTTP-EPISODES','Trang phim bộ có tập nguồn',r.status_code==200 and b'S01E' in r.data,r.status_code)
 finally:
  os.environ['DB_PASSWORD']=oldpass
  if olduser is None:os.environ.pop('DB_USER',None)
  else:os.environ['DB_USER']=olduser
  c.close()
 (ROOT/'evidence/sourced_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('SOURCED CHECKS',sum(x['passed'] for x in out),'/',len(out))
 for row in out:
  if not row['passed']:print(row)
 if not all(x['passed'] for x in out):raise SystemExit(1)
if __name__=='__main__':main()
