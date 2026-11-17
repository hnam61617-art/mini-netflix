"""Đo SELECT gốc trên dữ liệu nguồn, không tạo bất cứ fixture nào."""
import sys,json,time,statistics,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from verify import conn,statements
c=conn();bench=[];plans=[]
try:
 with c.cursor() as q:
  q.execute('SELECT VERSION(),UTC_TIMESTAMP(),@@transaction_isolation');version,tested,isolation=q.fetchone()
  q.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='mini_netflix' AND table_type='BASE TABLE'");tables=[r[0] for r in q.fetchall()];counts={}
  for table in tables:q.execute('SELECT COUNT(*) FROM '+table);counts[table]=q.fetchone()[0]
  q.execute('SET @profile_id=1')
  for i,(title,text) in enumerate(json.loads((ROOT/'queries.json').read_text()),1):
   pieces=list(statements(text))
   for sql in pieces[:-1]:q.execute(sql)
   samples=[]
   for run in range(35):
    start=time.perf_counter();q.execute(pieces[-1]);rows=q.fetchall();elapsed=(time.perf_counter()-start)*1000
    if run>=5:samples.append(elapsed)
   bench.append(dict(query='Q'+str(i),rows=len(rows),median_ms=round(statistics.median(samples),3),p95_ms=round(sorted(samples)[28],3)))
   q.execute('EXPLAIN ANALYZE '+pieces[-1]);plans.append(dict(query='Q'+str(i),plan=q.fetchall()))
finally:c.close()
for name,data in [('sourced_benchmark',bench),('sourced_explain_analyze',plans),('sourced_environment',dict(mysql=version,tested_at_utc=str(tested),isolation=isolation,python=platform.python_version(),table_counts=counts))]:
 (ROOT/'evidence'/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str))
print('BENCHMARK SOURCED: 10 SELECT, 5 warmups + 30 measurements each')
