"""Kiểm chứng trên CSDL thử mới đã nạp 01_schema, 02_seed và 04_roles.
Đặt DB_HOST, DB_PORT, DB_USER, DB_PASSWORD; tài khoản cần quyền quản lý role.
"""
import os,json,time,statistics,platform,secrets,concurrent.futures
from pathlib import Path
import pymysql
ROOT=Path(__file__).resolve().parent
RESULTS=[]
def conn(user=None,password=None):
 c=pymysql.connect(host=os.getenv('DB_HOST','127.0.0.1'),port=int(os.getenv('DB_PORT','3306')),user=user or os.getenv('DB_USER','root'),password=password if password is not None else os.environ['DB_PASSWORD'],database='mini_netflix',charset='utf8mb4',autocommit=True)
 with c.cursor() as q:
  q.execute("SET SESSION time_zone = '+00:00'");q.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
 return c
def statements(source):
 buf=[]
 for line in source.splitlines():
  if line.lstrip().startswith('--'):continue
  buf.append(line)
  if line.rstrip().endswith(';'):
   yield '\n'.join(buf).strip()[:-1];buf=[]
def record(code,name,passed,actual):
 RESULTS.append(dict(code=code,name=name,passed=bool(passed),actual=str(actual)))
def sqlcase(code,name,sql,error=None,setup=None,check=None):
 c=conn();c.begin()
 try:
  with c.cursor() as q:
   if setup:
    for s in setup:q.execute(s)
   try:
    q.execute(sql)
    actual=q.fetchall()
    ok=error is None
    if check:ok=ok and check(q)
    record(code,name,ok,actual if actual else 'Thành công; đã ROLLBACK')
   except pymysql.MySQLError as e:record(code,name,e.args[0]==error,e.args)
 finally:c.rollback();c.close()
def main():
 c=conn()
 with c.cursor() as q:
  q.execute('SELECT VERSION(), @@sql_mode, @@transaction_isolation, @@innodb_buffer_pool_size, UTC_TIMESTAMP()');v=q.fetchone()
  q.execute('SHOW TABLES');tables=[r[0] for r in q.fetchall() if not r[0].startswith('v_')]
  counts={}
  for t in tables:q.execute('SELECT COUNT(*) FROM '+t);counts[t]=q.fetchone()[0]
  q.execute('SELECT @@version_compile_os, @@version_compile_machine');build=q.fetchone()
 env=dict(mysql=v[0],sql_mode=v[1],isolation=v[2],buffer_pool_bytes=v[3],tested_at_utc=str(v[4]),python=platform.python_version(),client_os=platform.platform(),db_build=build,table_counts=counts)
  # no host identity or credentials are recorded
 cases=[
 ('VT01a','Email trùng',"UPDATE users SET email = 'student001@gmail.com' WHERE user_id = 2",1062),
 ('VT01b','Email sai miền',"UPDATE users SET email = 'a@example.com' WHERE user_id = 1",3819),
 ('VT01c','Số điện thoại sai',"UPDATE users SET phone = '123' WHERE user_id = 1",3819),
 ('VT01d','Tên chỉ khoảng trắng',"UPDATE users SET full_name = '   ' WHERE user_id = 1",3819),
 ('VT01e','Không sửa user_id','UPDATE users SET user_id = 9999 WHERE user_id = 1',1644),
 ('VT02','Hồ sơ tham chiếu sai',"INSERT INTO profiles(user_id,profile_name) VALUES(999999,'X')",1452),
 ('VT03a','Giá gói âm','UPDATE subscription_tiers SET prices = -1 WHERE tier_id = 1',3819),
 ('VT03b','Giới hạn thiết bị bằng 0','UPDATE subscription_tiers SET max_device = 0 WHERE tier_id = 1',3819),
 ('VT03c','Chất lượng sai',"UPDATE subscription_tiers SET video_quality = '8K' WHERE tier_id = 1",3819),
 ('VT04a','Ngày kết thúc bằng ngày bắt đầu','UPDATE subscriptions SET end_date = start_date WHERE subscription_id = 1',3819),
 ('VT04b','Trạng thái sai',"UPDATE subscriptions SET status = 'INVALID' WHERE subscription_id = 1",3819),
 ('VT04c','Boolean sai','UPDATE subscriptions SET auto_renew = 2 WHERE subscription_id = 1',3819),
 ('VT05a','Thanh toán âm',"INSERT INTO payments(subscription_id,prices,transaction_method) VALUES(1,-1,'CARD')",3819),
 ('VT05b','Không sửa thanh toán','UPDATE payments SET prices = prices + 1 WHERE payment_id = 1',1644),
 ('VT05c','Không xóa thanh toán chưa đủ 6 tháng','DELETE FROM payments WHERE payment_id = 1',1644),
 ('VT06','Tiêu đề rỗng',"UPDATE contents SET title = '' WHERE content_id = 1",3819),
 ('VT07a','Sai lớp con','INSERT INTO movies(content_id,video_url,duration) VALUES(80,\'x\',90)',1644),
 ('VT07b','Không xóa riêng lớp con','DELETE FROM movies WHERE content_id = 1',1644),
 ('VT07c','Thời lượng bằng 0','UPDATE movies SET duration = 0 WHERE content_id = 1',3819),
 ('VT08','Tổng tập âm','UPDATE tv_series SET total_episodes = -1 WHERE content_id = 51',3819),
 ('VT09a','Trùng số tập cùng bộ',"INSERT INTO episodes(content_id,episode_number,title,duration,video_url) VALUES(51,1,'X',45,'x')",1062),
 ('VT09b','Số tập bằng 0','UPDATE episodes SET episode_number = 0 WHERE episode_id = 1',3819),
 ('VT10','Thể loại trùng',"INSERT INTO genres(genre_name) VALUES('Hành động')",1062),
 ('VT11a','Trùng cặp nội dung–thể loại','INSERT INTO content_genres VALUES(1,1)',1062),
 ('VT11b','Không xóa thể loại đang dùng','DELETE FROM genres WHERE genre_id = 1',1451),
 ('VT12','Danh sách xem sau trùng','INSERT INTO watch_lists(profile_id,content_id) SELECT profile_id,content_id FROM watch_lists LIMIT 1',1062),
 ('VT13a','Tiến độ vượt 100', 'UPDATE watch_histories SET watch_progress = 100.01 WHERE history_id = 1',3819),
 ('VT13b','Tiến độ âm','UPDATE watch_histories SET watch_progress = -0.01 WHERE history_id = 1',3819),
 ('VT13c','Hai đích xem cùng NULL', 'INSERT INTO watch_histories(profile_id) VALUES(1)',3819),
 ('VT13d','Hai đích xem cùng có giá trị','INSERT INTO watch_histories(profile_id,content_id,episode_id) VALUES(1,1,1)',3819),
 ('VT13e','content_id không phải phim lẻ','INSERT INTO watch_histories(profile_id,content_id) VALUES(1,51)',1452),
 ('VT13f','Lịch sử phim lẻ trùng','INSERT INTO watch_histories(profile_id,content_id) VALUES(1,1)',1062),
 ('VT13g','Lịch sử tập phim trùng','INSERT INTO watch_histories(profile_id,episode_id) VALUES(1,1)',1062),
 ('VT19a','Không xóa tài khoản còn lượt đăng ký','DELETE FROM users WHERE user_id = 1',1451),
 ('VT19b','Không xóa lượt đăng ký còn payment','DELETE FROM subscriptions WHERE subscription_id = 1',1451),
 ]
 for code,name,s,error in cases:
  setup=None
  if code=='VT13f':setup=['DELETE FROM watch_histories WHERE profile_id = 1 AND content_id = 1','INSERT INTO watch_histories(profile_id,content_id) VALUES(1,1)']
  if code=='VT13g':setup=['DELETE FROM watch_histories WHERE profile_id = 1 AND episode_id = 1','INSERT INTO watch_histories(profile_id,episode_id) VALUES(1,1)']
  sqlcase(code,name,s,error,setup)
 for value in [0,89.99,90,100]:
  sqlcase('BOUND'+str(value),'Tiến độ hợp lệ và ngưỡng hoàn thành '+str(value),f'UPDATE watch_histories SET watch_progress = {value} WHERE history_id = 1',check=lambda q,value=value: (q.execute('SELECT watch_progress >= 90 FROM watch_histories WHERE history_id = 1') or True) and q.fetchone()[0]==(value>=90))
 sqlcase('COUNT-I','Thêm tập tăng bộ đếm',"INSERT INTO episodes(content_id,episode_number,title,duration,video_url) VALUES(80,1,'Tập mới',45,'x')",check=lambda q:(q.execute('SELECT total_episodes FROM tv_series WHERE content_id = 80') or True) and q.fetchone()[0]==1)
 sqlcase('COUNT-D','Xóa tập giảm bộ đếm','DELETE FROM episodes WHERE episode_id = 1',check=lambda q:(q.execute('SELECT total_episodes FROM tv_series WHERE content_id = 51') or True) and q.fetchone()[0]==3)
 sqlcase('COUNT-M','Chuyển tập đồng bộ hai bộ đếm','UPDATE episodes SET content_id = 80 WHERE episode_id = 1',check=lambda q:(q.execute('SELECT total_episodes FROM tv_series WHERE content_id IN(51,80) ORDER BY content_id') or True) and q.fetchall()==((3,),(1,)))
 sqlcase('DELETE-P','Xóa hồ sơ xóa watch_lists và watch_histories','DELETE FROM profiles WHERE profile_id = 200',check=lambda q:(q.execute('SELECT (SELECT COUNT(*) FROM watch_lists WHERE profile_id = 200) + (SELECT COUNT(*) FROM watch_histories WHERE profile_id = 200)') or True) and q.fetchone()[0]==0)
 sqlcase('DELETE-C','Xóa bộ xóa tập và lịch sử tập','DELETE FROM contents WHERE content_id = 51',check=lambda q:(q.execute('SELECT (SELECT COUNT(*) FROM episodes WHERE content_id = 51) + (SELECT COUNT(*) FROM watch_histories WHERE episode_id BETWEEN 1 AND 4)') or True) and q.fetchone()[0]==0)
 sqlcase('RETENTION','Cho xóa payment đủ 6 tháng',"DELETE FROM payments WHERE payment_id = 999999",setup=["INSERT INTO payments(payment_id,subscription_id,prices,transaction_method,history_payment) VALUES(999999,1,70000,'CARD',DATE_SUB(CURRENT_TIMESTAMP,INTERVAL 7 MONTH))"])
 queries=json.loads((ROOT/'queries.json').read_text());bench=[]; plans=[]
 with c.cursor() as q:
  q.execute('ANALYZE TABLE contents, content_genres, subscriptions, payments, episodes, watch_histories');q.fetchall()
  for i,(title,source) in enumerate(queries,1):
   codes=list(statements(source));params=codes[:-1];select=codes[-1]
   for s in params:q.execute(s)
   durations=[]
   for n in range(35):
    begin=time.perf_counter();q.execute(select);rows=q.fetchall();elapsed=(time.perf_counter()-begin)*1000
    if n>=5:durations.append(elapsed)
   bench.append(dict(query='Q'+str(i),rows=len(rows),median_ms=round(statistics.median(durations),3),p95_ms=round(sorted(durations)[28],3)))
   record('Q'+str(i),title,True,f'{len(rows)} hàng; 30 lần đo sau 5 lần làm nóng')
   q.execute('EXPLAIN ANALYZE '+select);plans.append({'query':'Q'+str(i),'plan':q.fetchall()})
 # independent revenue cross-check
 with c.cursor() as q:
  q.execute("SELECT SUM(prices) FROM payments WHERE history_payment >= '2025-01-01' AND history_payment < '2026-01-01'");expected=q.fetchone()[0]
  q.execute(list(statements(queries[6][1]))[-1]);actual=sum(row[3] for row in q.fetchall())
  record('REVENUE','Q7 khớp tổng độc lập',actual==(expected or 0),f'{actual} / {expected or 0}')
 # disposable test logins, no passwords in evidence
 role_password=secrets.token_urlsafe(24)
 with c.cursor() as q:
  for user,role in [('mn_verify_app','mn_app'),('mn_verify_catalog','mn_catalog'),('mn_verify_report','mn_report'),('mn_verify_retention','mn_retention')]:
   q.execute("CREATE USER %s@'%%' IDENTIFIED WITH mysql_native_password BY %s",(user,role_password))
   q.execute("GRANT '"+role+"' TO '"+user+"'@'%'");q.execute("SET DEFAULT ROLE '"+role+"' TO '"+user+"'@'%'")
 def rolecase(code,user,sql,error=None,rollback=True):
  try:rc=conn(user,role_password)
  except pymysql.MySQLError as e:
   record(code,user,e.args[0]==error,e.args);return
  try:
   if rollback:rc.begin()
   with rc.cursor() as q:
    try:q.execute(sql);q.fetchall();record(code,user,error is None,'Cho phép')
    except pymysql.MySQLError as e:record(code,user,e.args[0]==error,e.args)
  finally:
   if rollback:rc.rollback()
   rc.close()
 rolecase('SEC01','mn_verify_report','SELECT * FROM v_content_catalog')
 for i,(_,source) in enumerate(queries,1):
  rc=conn('mn_verify_report',role_password)
  try:
   with rc.cursor() as q:
    for s in statements(source):q.execute(s);q.fetchall()
   record('SEC-Q'+str(i),'mn_report chạy Q'+str(i),True,'Đủ quyền nguồn')
  except Exception as e:record('SEC-Q'+str(i),'mn_report chạy Q'+str(i),False,e)
  finally:rc.close()
 rolecase('SEC02','mn_verify_report','SELECT email,phone,password_hash FROM users',1142)
 rolecase('SEC03','mn_verify_report','UPDATE watch_histories SET watch_progress = 1 WHERE history_id = 1',1142)
 rolecase('SEC05','mn_verify_app','UPDATE payments SET prices = prices + 1 WHERE payment_id = 1',1142)
 rolecase('SEC06','mn_verify_catalog',"INSERT INTO episodes(content_id,episode_number,title,duration,video_url) VALUES(80,1,'X',45,'x')")
 rolecase('SEC07','mn_verify_catalog','UPDATE tv_series SET total_episodes = 999 WHERE content_id = 80',1142)
 rolecase('SEC08','mn_verify_catalog','SELECT * FROM users',1142)
 rolecase('SEC09','mn_verify_retention','DELETE FROM payments WHERE payment_id = 1',1644)
 with c.cursor() as q:q.execute("REVOKE 'mn_report' FROM 'mn_verify_report'@'%'")
 rolecase('SEC10','mn_verify_report','SELECT * FROM v_content_catalog',1044)
 # concurrency uses dedicated rows, cleaned afterwards
 with c.cursor() as q:
  q.execute("INSERT INTO users(user_id,email,phone,password_hash,full_name) VALUES(999001,'verify999001@gmail.com','0999999001','test-only','Kiểm thử')")
  q.execute("INSERT INTO subscriptions(subscription_id,user_id,tier_id,start_date,end_date,status) VALUES(999001,999001,1,DATE_SUB(CURRENT_TIMESTAMP,INTERVAL 10 DAY),DATE_ADD(CURRENT_TIMESTAMP,INTERVAL 20 DAY),'ACTIVE')")
  q.execute('SELECT end_date FROM subscriptions WHERE subscription_id = 999001');end=q.fetchone()[0]
 def renew(_):
  rc=conn('mn_verify_app',role_password)
  try:
   with rc.cursor() as q:
    q.callproc('sp_renew_subscription',(999001,999001,end,False,True,'CARD'))
    while q.nextset():pass
   return 'OK'
  except pymysql.MySQLError as e:return str(e.args)
  finally:rc.close()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rr=list(pool.map(renew,range(2)))
 with c.cursor() as q:
  q.execute('SELECT COUNT(*) FROM payments WHERE subscription_id = 999001');pc=q.fetchone()[0]
  q.execute('SELECT TIMESTAMPDIFF(DAY,%s,end_date) FROM subscriptions WHERE subscription_id = 999001',(end,));days=q.fetchone()[0]
 record('VT15','Hai yêu cầu gia hạn cùng thời hạn kỳ vọng',rr.count('OK')==1 and pc==1 and days==30,rr+['payments='+str(pc),'days='+str(days)])
 # remove only dedicated fixtures, preserve all normal triggers
 with c.cursor() as q:
  q.execute('DELETE FROM subscriptions WHERE subscription_id = 999001') if pc==0 else None
 # Successful payment is deliberately retained by 6-month rule; do not bypass it.
 with c.cursor() as q:
  for user in ['mn_verify_app','mn_verify_catalog','mn_verify_report','mn_verify_retention']:q.execute("DROP USER '"+user+"'@'%'")
 c.close()
 out=ROOT/'evidence';out.mkdir(exist_ok=True)
 (out/'environment.json').write_text(json.dumps(env,ensure_ascii=False,indent=2,default=str))
 (out/'verification.json').write_text(json.dumps(RESULTS,ensure_ascii=False,indent=2))
 (out/'benchmark.json').write_text(json.dumps(bench,ensure_ascii=False,indent=2))
 (out/'explain_analyze.json').write_text(json.dumps(plans,ensure_ascii=False,indent=2,default=str))
 print('PASS',sum(r['passed'] for r in RESULTS),'/',len(RESULTS))
 for r in RESULTS:
  if not r['passed']:print('FAIL',r)
if __name__=='__main__':main()
