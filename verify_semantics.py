"""Bốn ca kết quả nghiệp vụ có dữ liệu đối chứng, ROLLBACK sau mỗi ca."""
import json
from pathlib import Path
from verify import conn,statements
ROOT=Path(__file__).resolve().parent
def main():
 queries=json.loads((ROOT/'queries.json').read_text());out=[];c=conn()
 def record(code,name,ok,actual):out.append(dict(code=code,name=name,passed=bool(ok),actual=str(actual)))
 def run(q,index):
  for s in statements(queries[index-1][1]):q.execute(s)
  return q.fetchall()
 try:
  c.begin()
  with c.cursor() as q:
   q.execute("INSERT INTO profiles(profile_id,user_id,profile_name) VALUES(999002,3,'Hồ sơ đối chứng')")
   q.execute('''INSERT INTO watch_histories(profile_id,content_id,episode_id,watch_progress)
   SELECT 999002,IF(c.content_type='MOVIE',c.content_id,NULL),
          IF(c.content_type='TV_SERIES',(SELECT MIN(e.episode_id) FROM episodes AS e WHERE e.content_id=c.content_id),NULL),50
   FROM contents AS c JOIN content_genres AS cg ON cg.content_id=c.content_id
   WHERE cg.genre_id=1''')
   rows=run(q,8);record('FUNC08','Q8 có kết quả khi hồ sơ xem đủ thể loại',any(r[0]==999002 for r in rows),len(rows))
  c.rollback();c.begin()
  with c.cursor() as q:
   rows=run(q,4);r=next(r for r in rows if r[0]==80);record('FUNC04','Q4 bộ 0 tập chưa hoàn thành',r[2]==0 and r[-1]==0,r)
  c.rollback();c.begin()
  with c.cursor() as q:
   q.execute("INSERT INTO users(user_id,email,phone,password_hash,full_name) VALUES(999003,'verify999003@gmail.com','0999999003','test-only','Đối chứng')")
   q.execute("INSERT INTO subscriptions(user_id,tier_id,start_date,end_date,status) VALUES(999003,1,CURRENT_TIMESTAMP,DATE_ADD(CURRENT_TIMESTAMP,INTERVAL 30 DAY),'ACTIVE')")
   rows=run(q,10);record('FUNC10','Q10 tìm tài khoản còn gói và chưa xem',any(r[0]==999003 for r in rows),len(rows))
  c.rollback();c.begin()
  with c.cursor() as q:
   q.execute('''SELECT c.content_id,COUNT(DISTINCT x.profile_id) FROM contents AS c JOIN (
       SELECT profile_id,content_id FROM watch_histories WHERE content_id IS NOT NULL AND watch_progress>0
       UNION
       SELECT wh.profile_id,e.content_id FROM watch_histories AS wh JOIN episodes AS e ON e.episode_id=wh.episode_id WHERE wh.watch_progress>0
   ) AS x ON x.content_id=c.content_id GROUP BY c.content_id''');expected=dict(q.fetchall())
   rows=run(q,3);record('FUNC03','Q3 đếm hồ sơ, không đếm lặp các tập',all(expected[r[0]]==r[2] for r in rows),len(rows))
  c.rollback()
 finally:c.rollback();c.close()
 (ROOT/'evidence/semantic_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print('SEMANTIC PASS',sum(x['passed'] for x in out),'/',len(out))
if __name__=='__main__':main()
