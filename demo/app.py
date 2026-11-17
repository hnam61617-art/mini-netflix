"""Ứng dụng demo cục bộ cho đồ án Mini-Netflix; dùng mn_app, không dùng root."""
import os,secrets,threading,time
from functools import wraps
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor
from flask import Flask,request,session,redirect,url_for,render_template_string,render_template,abort,flash
from werkzeug.security import check_password_hash

app=Flask(__name__)
app.secret_key=os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax')
sessions={};session_lock=threading.Lock();HEARTBEAT_TIMEOUT=120
def db():
 c=pymysql.connect(host=os.getenv('DB_HOST','127.0.0.1'),port=int(os.getenv('DB_PORT','3306')),user=os.getenv('DB_USER','mn_service'),password=os.environ['DB_PASSWORD'],database='mini_netflix',charset='utf8mb4',cursorclass=DictCursor,autocommit=False)
 with c.cursor() as q:
  q.execute("SET SESSION time_zone = '+00:00'");q.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED')
 return c
def csrf():
 if 'csrf' not in session:session['csrf']=secrets.token_hex(24)
 return session['csrf']
app.jinja_env.globals['csrf']=csrf
@app.before_request
def check_csrf():
 if request.method=='POST' and not secrets.compare_digest(request.form.get('csrf',''),session.get('csrf','missing')):abort(400,'Yêu cầu không hợp lệ')
def login_required(f):
 @wraps(f)
 def wrapped(*a,**kw):
  if 'user_id' not in session:return redirect(url_for('login'))
  return f(*a,**kw)
 return wrapped
def own(q,pid):
 q.execute('SELECT * FROM profiles WHERE profile_id = %s AND user_id = %s',(pid,session['user_id']))
 if not q.fetchone():abort(403,'Hồ sơ không thuộc tài khoản')
def active(q):
 q.execute('SELECT * FROM v_active_subscriptions WHERE user_id = %s',(session['user_id'],));s=q.fetchone()
 if not s:abort(403,'Gói dịch vụ đã hết hiệu lực')
 return s
STYLE='''<style>body{font-family:Arial,sans-serif;max-width:1050px;margin:32px auto;background:#f6f7fb;color:#172034;padding:20px}h1{color:#a31825}section,form.panel{background:white;padding:20px;border-radius:10px;margin:15px 0}input,select,button{padding:9px;margin:5px;border:1px solid #bcc4ce;border-radius:5px}button{background:#a31825;color:white;cursor:pointer}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:9px;border-bottom:1px solid #ddd}.muted{color:#596675}</style>'''
STYLE += '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/static/style.css"><title>Mini-Netflix · Nhóm G2</title>'
@app.route('/login',methods=['GET','POST'])
def login():
 error=''
 if request.method=='POST':
  c=db()
  try:
   with c.cursor() as q:q.execute('SELECT user_id,password_hash FROM users WHERE email = %s',(request.form.get('email',''),));u=q.fetchone()
  finally:c.close()
  if u and check_password_hash(u['password_hash'],request.form.get('password','')):
   session.clear();session['user_id']=u['user_id'];csrf();return redirect(url_for('index'))
  error='Email hoặc mật khẩu chưa đúng'
 return render_template('consumer/auth.html',register=False,error=error)
@app.post('/logout')
def logout():session.clear();return redirect(url_for('login'))
@app.get('/')
@login_required
def index():
 from consumer import home
 return home()
@app.post('/profiles')
@login_required
def add_profile():
 name=request.form.get('profile_name','').strip()
 if not name or len(name)>50:abort(400,'Tên hồ sơ không hợp lệ')
 c=db()
 try:
  with c.cursor() as q:
   q.execute('SELECT user_id FROM users WHERE user_id=%s FOR UPDATE',(session['user_id'],))
   q.execute('SELECT max_profile FROM v_active_subscriptions WHERE user_id=%s',(session['user_id'],));s=q.fetchone()
   q.execute('SELECT COUNT(*) AS n FROM profiles WHERE user_id=%s',(session['user_id'],));n=q.fetchone()['n']
   if n>=(s['max_profile'] if s else 1):abort(409,'Đã đạt giới hạn hồ sơ')
   q.execute('INSERT INTO profiles(user_id,profile_name) VALUES(%s,%s)',(session['user_id'],name));c.commit()
 finally:c.rollback();c.close()
 return redirect(url_for('index'))
@app.post('/watch-list')
@app.post('/watch-list/delete')
@login_required
def change_list():
 pid=request.form.get('profile_id',type=int);cid=request.form.get('content_id',type=int);c=db()
 try:
  with c.cursor() as q:
   own(q,pid)
   if request.path.endswith('/delete'):q.execute('DELETE FROM watch_lists WHERE profile_id=%s AND content_id=%s',(pid,cid))
   else:
    q.execute('SELECT content_id FROM contents WHERE content_id=%s',(cid,))
    if not q.fetchone():abort(400,'Nội dung không tồn tại')
    try:q.execute('INSERT INTO watch_lists(profile_id,content_id) VALUES(%s,%s)',(pid,cid))
    except pymysql.IntegrityError as e:
     if e.args[0]!=1062:raise
   c.commit()
 finally:c.rollback();c.close()
 return redirect(url_for('content_detail',cid=cid,profile_id=pid)) if request.form.get('return_detail')=='1' else redirect(url_for('index',profile_id=pid))
@app.post('/progress')
@login_required
def progress():
 pid=request.form.get('profile_id',type=int)
 try:kind,key=request.form.get('target','').split(':');key=int(key);value=float(request.form['watch_progress'])
 except (ValueError,KeyError):abort(400,'Tiến độ không hợp lệ')
 if kind not in ('movie','episode') or not 0<=value<=100:abort(400,'Tiến độ không hợp lệ')
 c=db()
 try:
  with c.cursor() as q:
   own(q,pid);active(q)
   q.execute('SELECT profile_id FROM profiles WHERE profile_id=%s FOR UPDATE',(pid,))
   column='content_id' if kind=='movie' else 'episode_id'
   q.execute('SELECT '+column+' FROM '+('movies' if kind=='movie' else 'episodes')+' WHERE '+column+'=%s FOR SHARE',(key,))
   if not q.fetchone():abort(400,'Phim hoặc tập không tồn tại')
   q.execute('SELECT history_id FROM watch_histories WHERE profile_id=%s AND '+column+'=%s',(pid,key));h=q.fetchone()
   if h:q.execute('UPDATE watch_histories SET watch_progress=%s,last_watch_at=CURRENT_TIMESTAMP WHERE history_id=%s',(value,h['history_id']))
   else:q.execute('INSERT INTO watch_histories(profile_id,'+column+',watch_progress) VALUES(%s,%s,%s)',(pid,key,value))
   c.commit()
 finally:c.rollback();c.close()
 if request.form.get('return_detail')=='1':
  if kind=='movie':cid=key
  else:
   c=db()
   try:
    with c.cursor() as q:q.execute('SELECT content_id FROM episodes WHERE episode_id=%s',(key,));cid=q.fetchone()['content_id']
   finally:c.close()
  return redirect(url_for('content_detail',cid=cid,profile_id=pid,episode_id=key if kind=='episode' else None))
 return redirect(url_for('index',profile_id=pid))
@app.post('/renew')
@login_required
def renew():
 try:expected=datetime.fromisoformat(request.form['expected_end']);sid=int(request.form['subscription_id'])
 except (KeyError,ValueError):abort(400,'Yêu cầu gia hạn không hợp lệ')
 c=db()
 try:
  # No previous business transaction; procedure manages COMMIT/ROLLBACK itself.
  with c.cursor() as q:
   q.callproc('sp_renew_subscription',(session['user_id'],sid,expected,False,True,'E_WALLET'))
   while q.nextset():pass
 except pymysql.MySQLError:abort(409,'Không thể gia hạn: yêu cầu cũ hoặc không hợp lệ')
 finally:c.close()
 flash('Đã gia hạn thêm 30 ngày và ghi nhận thanh toán mô phỏng.')
 return redirect(url_for('account')) if request.form.get('return_account')=='1' else redirect(url_for('index'))
@app.post('/play-session')
@login_required
def play_session():
 device=request.form.get('device_id','').strip();quality=request.form.get('video_quality','SD');pid=request.form.get('profile_id',type=int)
 if not device or len(device)>100 or quality not in ('SD','HD','4K'):abort(400)
 c=db()
 try:
  with c.cursor() as q:own(q,pid);s=active(q)
 finally:c.close()
 if ['SD','HD','4K'].index(quality)>['SD','HD','4K'].index(s['video_quality']):abort(403,'Vượt chất lượng gói')
 now=time.monotonic();uid=session['user_id']
 with session_lock:
  current=sessions.setdefault(uid,{})
  for d in list(current):
   if now-current[d]>HEARTBEAT_TIMEOUT:del current[d]
  if device not in current and len(current)>=s['max_device']:abort(409,'Vượt số thiết bị đồng thời')
  current[device]=now
 return {'status':'ACTIVE','heartbeat_seconds':60,'timeout_seconds':HEARTBEAT_TIMEOUT}
@app.errorhandler(pymysql.MySQLError)
def database_error(e):return 'Dữ liệu hoặc thao tác không hợp lệ; giao dịch không được ghi nhận.',409
import sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]))
# Keep one app instance when started with python demo/app.py.
sys.modules.setdefault('app',sys.modules[__name__])
import lab
import consumer
if __name__=='__main__':app.run(host=os.getenv('FLASK_HOST','127.0.0.1'),port=5000,debug=False)
