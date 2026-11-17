"""Phòng trình bày cục bộ, chỉ bật bằng LAB_ENABLED=1 và khóa LAB_KEY."""
import os,secrets
from pathlib import Path
from flask import request,session,abort,render_template,redirect
import pymysql
from app import app,db,login_required
import catalog
ROOT=Path(__file__).resolve().parents[1]
TABLES=['users','profiles','subscription_tiers','subscriptions','payments','contents','movies','tv_series','episodes','genres','content_genres','watch_lists','watch_histories']
def connection(kind='REPORT'):
 return pymysql.connect(host=os.getenv('DB_HOST','127.0.0.1'),port=int(os.getenv('DB_PORT','3306')),user=os.environ['LAB_'+kind+'_USER'],password=os.environ['LAB_'+kind+'_PASSWORD'],database='mini_netflix',charset='utf8mb4',autocommit=False,init_command="SET time_zone='+00:00'")
def guard():
 if os.getenv('LAB_ENABLED')!='1':abort(404)
 if not session.get('lab'):abort(403,'Mở /lab/login và nhập khóa phòng dữ liệu')
@app.route('/lab/login',methods=['GET','POST'])
@login_required
def lab_login():
 if os.getenv('LAB_ENABLED')!='1':abort(404)
 if request.method=='POST':
  key=os.getenv('LAB_KEY','')
  if not key or not secrets.compare_digest(key,request.form.get('key','')):abort(403)
  session['lab']=True;return redirect('/lab')
 return render_template('lab_login.html')
@app.route('/lab')
@login_required
def lab_home():
 guard();c=connection();counts={}
 try:
  with c.cursor() as q:
   for table in TABLES:
    if table=='users':continue
    q.execute('SELECT COUNT(*) FROM '+table);counts[table]=q.fetchone()[0]
   a=db()
   try:
    with a.cursor() as aq:aq.execute('SELECT COUNT(*) AS n FROM users');counts['users']=aq.fetchone()['n']
   finally:a.close()
 finally:c.close()
 return render_template('lab.html',title='Tổng quan',page='home',counts=counts,total=sum(counts.values()))
@app.get('/lab/data')
@login_required
def lab_data():
 guard();return redirect('/lab/search')
@app.get('/lab/query')
@login_required
def lab_query():
 guard();return redirect('/lab/search')
@app.route('/lab/catalog',methods=['GET','POST'])
@login_required
def lab_catalog():
 guard();message=''
 if request.method=='POST':
  try:
   if request.form.get('action')=='content':
    cid=catalog.create_content(request.form['title'],request.form['content_type'],[int(g) for g in request.form.getlist('genres')],request.form.get('video_url'),int(request.form.get('duration',100)),connection_factory=lambda:connection('CATALOG'));message=f'Đã thêm nội dung #{cid}. Có thể kiểm tra trong bảng contents.'
   else:
    c=connection('CATALOG')
    try:
     with c.cursor() as q:
      q.execute("SELECT content_id FROM contents WHERE content_type='TV_SERIES' AND content_id=%s FOR UPDATE",(int(request.form['content_id']),))
      if not q.fetchone():raise ValueError('Phim bộ không tồn tại')
      q.execute('INSERT INTO episodes(content_id,episode_number,title,duration,video_url) VALUES(%s,%s,%s,%s,%s)',(int(request.form['content_id']),int(request.form['episode_number']),request.form['title'],int(request.form['duration']),request.form['video_url']))
      c.commit();message='Đã thêm tập. Trigger đã tăng total_episodes.'
    except Exception:c.rollback();raise
    finally:c.close()
  except (ValueError,KeyError,pymysql.MySQLError):message='Không ghi dữ liệu: kiểm tra trường bắt buộc, thời lượng, thể loại hoặc số tập trùng.'
 c=connection('CATALOG')
 try:
  with c.cursor(pymysql.cursors.DictCursor) as q:
   q.execute('SELECT * FROM genres');genres=q.fetchall();q.execute("SELECT content_id,title FROM contents WHERE content_type='TV_SERIES' ORDER BY content_id");series=q.fetchall()
 finally:c.close()
 return render_template('lab.html',title='Thêm nội dung',page='catalog',genres=genres,series=series,message=message)

import management
