"""Kiểm thử HTTP bằng Flask test client và MySQL thật, sau verify.py.
Tài khoản DB_USER/DB_PASSWORD cần quyền quản trị để tạo tài khoản thử tạm.
"""
import os,sys,json,secrets,re,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'demo'))
import app as demo
import catalog
from verify import conn

def main():
 admin=conn();password=secrets.token_urlsafe(24);out=[]
 def record(code,name,ok,actual):out.append(dict(code=code,name=name,passed=bool(ok),actual=str(actual)))
 with admin.cursor() as q:
  for u,r in [('mn_http_app','mn_app'),('mn_http_catalog','mn_catalog')]:
   q.execute("CREATE USER %s@'%%' IDENTIFIED WITH mysql_native_password BY %s",(u,password));q.execute("GRANT '"+r+"' TO '"+u+"'@'%'");q.execute("SET DEFAULT ROLE '"+r+"' TO '"+u+"'@'%'")
 original_user=os.getenv('DB_USER');original_password=os.environ['DB_PASSWORD']
 os.environ['DB_USER']='mn_http_app';os.environ['DB_PASSWORD']=password
 client=demo.app.test_client()
 def token():
  with client.session_transaction() as s:return s['csrf']
 def post(path,**kw):return client.post(path,data=dict(csrf=token(),**kw))
 r=client.get('/login');record('APP01','Trang đăng nhập',r.status_code==200,r.status_code)
 r=client.post('/login',data={'email':'student001@gmail.com','password':'MiniNetflix1313!'});record('APP02','Từ chối thiếu CSRF',r.status_code==400,r.status_code)
 r=post('/login',email='student001@gmail.com',password='wrong');record('APP03','Từ chối sai mật khẩu',b'Email' in r.data and r.status_code==200,r.status_code)
 r=post('/login',email='student001@gmail.com',password='MiniNetflix1313!');record('APP04','Đăng nhập bằng mật khẩu đã băm',r.status_code==302,r.status_code)
 r=client.get('/');record('APP05','Đọc danh mục và lịch sử từ MySQL',r.status_code==200 and 'Phim lẻ'.encode() in r.data,r.status_code)
 r=client.get('/?profile_id=3');record('APP06','Không đọc hồ sơ tài khoản khác',r.status_code==403,r.status_code)
 r=post('/watch-list',profile_id=3,content_id=1);record('APP07','Không sửa danh sách hồ sơ khác',r.status_code==403,r.status_code)
 r=post('/profiles',profile_name='Hồ sơ vượt giới hạn');record('APP08','Không tạo quá max_profile',r.status_code==409,r.status_code)
 with admin.cursor() as q:q.execute('SELECT content_id FROM watch_lists WHERE profile_id=1 ORDER BY content_id LIMIT 1');cid=q.fetchone()[0]
 r=post('/watch-list',profile_id=1,content_id=cid);record('APP09','Thêm lại xem sau không sinh bản ghi trùng',r.status_code==302,r.status_code)
 r=post('/progress',profile_id=1,target='movie:1',watch_progress='100.01');record('APP10','Từ chối tiến độ vượt miền',r.status_code==400,r.status_code)
 with admin.cursor() as q:q.execute('SELECT history_id,watch_progress,last_watch_at FROM watch_histories WHERE profile_id=1 AND content_id=1');old=q.fetchone()
 r=post('/progress',profile_id=1,target='movie:1',watch_progress='90');record('APP11','Ghi tiến độ hợp lệ qua ứng dụng',r.status_code==302,r.status_code)
 with admin.cursor() as q:
  q.execute('SELECT COUNT(*),MIN(watch_progress) FROM watch_histories WHERE profile_id=1 AND content_id=1');row=q.fetchone();record('APP12','Duy nhất lịch sử phim và hoàn thành tại 90%',row==(1,90),row)
  if old:q.execute('UPDATE watch_histories SET watch_progress=%s,last_watch_at=%s WHERE history_id=%s',(old[1],old[2],old[0]))
  else:q.execute('DELETE FROM watch_histories WHERE profile_id=1 AND content_id=1')
 r=post('/play-session',profile_id=1,device_id='A',video_quality='4K');record('APP13','Không vượt chất lượng SD của gói cơ bản',r.status_code==403,r.status_code)
 r=post('/play-session',profile_id=1,device_id='A',video_quality='SD');record('APP14','Mở phiên đúng giới hạn',r.status_code==200,r.status_code)
 r=post('/play-session',profile_id=1,device_id='B',video_quality='SD');record('APP15','Từ chối thiết bị thứ hai của gói 1 thiết bị',r.status_code==409,r.status_code)
 demo.sessions[1]['A']-=121
 r=post('/play-session',profile_id=1,device_id='B',video_quality='SD');record('APP16','Phiên hết heartbeat được loại khỏi bộ đếm',r.status_code==200,r.status_code)
 post('/logout');client.get('/login');post('/login',email='student061@gmail.com',password='MiniNetflix1313!')
 r=post('/progress',profile_id=121,target='movie:1',watch_progress='90');record('APP17','Hết hạn gói không được ghi tiến độ xem',r.status_code==403,r.status_code)
 os.environ['DB_USER']='mn_http_catalog'
 try:catalog.create_content('Sai thể loại','MOVIE',[],video_url='x',duration=90);ok=False
 except ValueError:ok=True
 record('APP18','Tạo nội dung thiếu thể loại bị từ chối',ok,'ValueError' if ok else 'Không bị từ chối')
 cid=catalog.create_content('Nội dung kiểm thử','MOVIE',[1],video_url='x',duration=90)
 try:catalog.remove_genre(cid,1);ok=False
 except ValueError:ok=True
 record('APP19','Không gỡ thể loại cuối cùng',ok,'ROLLBACK' if ok else 'Không bị từ chối')
 with admin.cursor() as q:
  q.execute('SELECT (SELECT COUNT(*) FROM movies WHERE content_id=%s),(SELECT COUNT(*) FROM content_genres WHERE content_id=%s)',(cid,cid));row=q.fetchone();record('APP20','Tạo nội dung có đúng lớp con và thể loại',row==(1,1),row)
  q.execute('DELETE FROM contents WHERE content_id=%s',(cid,))
  for u in ['mn_http_app','mn_http_catalog']:q.execute("DROP USER '"+u+"'@'%'")
 admin.close()
 if original_user is None:os.environ.pop('DB_USER',None)
 else:os.environ['DB_USER']=original_user
 os.environ['DB_PASSWORD']=original_password
 (ROOT/'evidence/demo_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print('APP PASS',sum(x['passed'] for x in out),'/',len(out))
 for x in out:
  if not x['passed']:print(x)
if __name__=='__main__':main()
