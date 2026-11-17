"""Tra cứu nghiệp vụ có tham số; kết quả báo cáo dùng chính SELECT từ queries.json."""
import json
from datetime import date,timedelta
from pathlib import Path
from flask import request,session,render_template,abort
from app import app,db,login_required
from verify import statements
from lab import guard
QUERIES=json.loads((Path(__file__).resolve().parents[1]/'queries.json').read_text())
TASKS={
 'users':dict(title='Tìm người dùng',group='Thông tin',hint='Nhập ID, họ tên, email hoặc số điện thoại. Đăng nhập không tạo tài khoản mới; đăng ký mới tạo bản ghi users.',fields=['user_id','term']),
 'profiles':dict(title='Tìm hồ sơ',group='Thông tin',hint='Tìm theo mã hồ sơ, tài khoản chủ sở hữu hoặc tên hồ sơ / họ tên người dùng.',fields=['profile_id','user_id','term']),
 'contents':dict(title='Tìm phim & nội dung',group='Thông tin',hint='Nhập tên hoặc ID nội dung, hoặc chọn loại phim / thể loại. Các điều kiện kết hợp với nhau.',fields=['content_id','term','content_type','genre_id']),
 'catalog':dict(title='Phim theo thể loại & ngày phát hành',group='Nội dung',q=1,hint='Chọn thể loại, loại phim và khoảng ngày phát hành chính xác. Phim nguồn chỉ có năm sẽ không khớp bộ lọc ngày; dùng Tìm phim & nội dung để tìm theo tên/thể loại.',fields=['genre_id','content_type','date_from','date_to']),
 'monthly':dict(title='Doanh thu từng tháng & tăng trưởng',group='Doanh thu',q=2,hint='Tổng doanh thu và mức tăng trưởng so với tháng liền trước trong khoảng ngày đã chọn.',fields=['date_from','date_to']),
 'ranking':dict(title='Xếp hạng nội dung được xem',group='Nội dung',q=3,hint='Đếm hồ sơ đã bắt đầu xem, không đếm lặp tập. Lọc tên/ID trong bảng xếp hạng; đồng hạng có thể có nhiều dòng.',fields=['top_n','content_id','term']),
 'series_progress':dict(title='Tiến độ phim bộ của hồ sơ',group='Hồ sơ',q=4,hint='Nhập đúng mã hồ sơ; có thể thêm ID hoặc tên phim bộ để xem riêng một nội dung.',fields=['profile_id','content_id','term']),
 'pending_list':dict(title='Xem sau chưa hoàn thành',group='Hồ sơ',q=5,hint='Nhập mã hồ sơ để xem những nội dung đã lưu nhưng chưa hoàn thành.',fields=['profile_id','content_id','term']),
 'due':dict(title='Đăng ký đến hạn xử lý',group='Gói dịch vụ',q=6,hint='Tìm các lượt ACTIVE đã đến hạn. Nhập mã người dùng để tìm riêng; có thể lọc tự gia hạn.',fields=['user_id','auto_renew']),
 'tier_revenue':dict(title='Doanh thu theo gói dịch vụ',group='Doanh thu',q=7,hint='Chọn khoảng ngày, tùy chọn một gói; hiển thị số thanh toán và doanh thu đúng gói.',fields=['date_from','date_to','tier_id']),
 'genre_completion':dict(title='Hồ sơ đã xem đủ thể loại',group='Hồ sơ',q=8,hint='Chọn thể loại để tìm hồ sơ đã bắt đầu xem mọi nội dung thuộc thể loại đó. Có thể tìm riêng một hồ sơ.',fields=['genre_id','profile_id']),
 'genre_ranking':dict(title='Nội dung nổi bật theo thể loại',group='Nội dung',q=9,hint='Chọn thể loại và số hạng để xếp hạng nội dung theo số hồ sơ xem; giữ đồng hạng.',fields=['genre_id','top_n','term']),
 'inactive':dict(title='Tài khoản có gói nhưng ít hoạt động',group='Gói dịch vụ',q=10,hint='Tìm tài khoản còn gói nhưng chưa xem trong số ngày đã nhập; tùy chọn một người dùng.',fields=['days','user_id']),
}
LABELS={'user_id':'Mã người dùng','full_name':'Họ và tên','email':'Email','phone':'Điện thoại','created_at':'Ngày tạo','profile_id':'Mã hồ sơ','profile_name':'Tên hồ sơ','content_id':'Mã nội dung','title':'Tiêu đề','content_type':'Loại nội dung','date_released':'Ngày phát hành','movie_duration':'Thời lượng (phút)','total_episodes':'Số tập','genre_names':'Thể loại','month_start':'Tháng','revenue':'Doanh thu (đ)','growth_percent':'Tăng trưởng (%)','viewer_profiles':'Hồ sơ đã xem','rank_no':'Hạng','episode_count':'Tổng tập','completed_episodes':'Tập hoàn thành','completed_percent':'Hoàn thành (%)','is_completed':'Đã hoàn thành','added_at':'Ngày thêm','subscription_id':'Mã đăng ký','end_date':'Hết hạn','auto_renew':'Tự gia hạn','tier_id':'Mã gói','tier_name':'Tên gói','payment_count':'Số thanh toán','genre_name':'Thể loại'}

def integer(values,key,required=False,minimum=1,maximum=2147483647):
 raw=values.get(key,'').strip()
 if not raw:
  if required:raise ValueError('Cần nhập '+LABELS.get(key,key).lower())
  return None
 try:value=int(raw)
 except ValueError:raise ValueError('Giá trị số chưa hợp lệ: '+LABELS.get(key,key))
 if not minimum<=value<=maximum:raise ValueError('Giá trị ngoài khoảng cho phép: '+LABELS.get(key,key))
 return value

def build(values):
 task=values['task'];meta=TASKS[task];clauses=[];params=[];ids={}
 for key in ['user_id','profile_id','content_id','genre_id','tier_id']:
  if key in meta['fields']:ids[key]=integer(values,key)
 term=values.get('term','').strip()[:255]
 kind=values.get('content_type','')
 if kind and kind not in ('MOVIE','TV_SERIES'):raise ValueError('Loại phim chưa hợp lệ')
 def where(sql,*args):clauses.append(sql);params.extend(args)
 if task=='users':
  source='SELECT u.user_id,u.full_name,u.email,u.phone,u.created_at FROM users u'
  if ids.get('user_id'):where('u.user_id=%s',ids['user_id'])
  if term:where('(u.full_name LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)',*(['%'+term+'%']*3))
  if not clauses:raise ValueError('Nhập ID, họ tên, email hoặc số điện thoại; hoặc bấm Tài khoản đang đăng nhập.')
  order='u.user_id'
 elif task=='profiles':
  source='SELECT p.profile_id,p.profile_name,p.user_id,u.full_name,u.email,p.created_at FROM profiles p JOIN users u ON u.user_id=p.user_id'
  if ids.get('user_id'):where('p.user_id=%s',ids['user_id'])
  if ids.get('profile_id'):where('p.profile_id=%s',ids['profile_id'])
  if term:where('(p.profile_name LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s)',*(['%'+term+'%']*3))
  if not clauses:raise ValueError('Nhập mã hồ sơ, mã người dùng hoặc tên để tìm hồ sơ cụ thể.')
  order='p.profile_id'
 elif task=='contents':
  source='SELECT c.content_id,c.title,c.content_type,c.date_released,c.movie_duration,c.total_episodes,c.genre_names FROM v_content_catalog c'
  if ids.get('content_id'):where('c.content_id=%s',ids['content_id'])
  if term:where('c.title LIKE %s','%'+term+'%')
  if kind:where('c.content_type=%s',kind)
  if ids.get('genre_id'):where('EXISTS(SELECT 1 FROM content_genres cg WHERE cg.content_id=c.content_id AND cg.genre_id=%s)',ids['genre_id'])
  if not clauses:raise ValueError('Nhập ID/tên phim hoặc chọn ít nhất một điều kiện loại phim, thể loại.')
  order='c.content_id'
 else:
  number=meta['q'];sql=list(statements(QUERIES[number-1][1]))[-1]
  setups={}
  if 'date_from' in meta['fields']:
   try:start=date.fromisoformat(values.get('date_from',''));end=date.fromisoformat(values.get('date_to',''))
   except ValueError:raise ValueError('Nhập ngày bắt đầu và kết thúc hợp lệ.')
   if end<start:raise ValueError('Ngày kết thúc phải bằng hoặc sau ngày bắt đầu.')
   setups.update(from_date=start,to_date=end+timedelta(days=1))
  if 'genre_id' in meta['fields']:
   if not ids.get('genre_id'):raise ValueError('Cần chọn một thể loại.')
   setups['genre_id']=ids['genre_id']
  if number in (4,5):
   if not ids.get('profile_id'):raise ValueError('Cần nhập mã hồ sơ cụ thể.')
   setups['profile_id']=ids['profile_id']
  if number in (2,7):sql=sql.replace("'2025-01-01'",'@from_date').replace("'2026-01-01'",'@to_date')
  if number==1:
   setups['content_type']=kind or 'MOVIE';sql=sql.replace("c.content_type = 'MOVIE'",'c.content_type = CONVERT(@content_type USING utf8mb4) COLLATE utf8mb4_0900_as_cs')
  if number in (3,9):
   setups['top_n']=integer(values,'top_n',True,1,50);sql=sql.replace('rank_no <= 10','rank_no <= @top_n').replace('rank_no <= 3','rank_no <= @top_n')
  if number==10:
   setups['days']=integer(values,'days',True,1,3650);sql=sql.replace('INTERVAL 30 DAY','INTERVAL @days DAY')
  source='SELECT r.*'+(',u.full_name,u.email' if number in (6,10) else '')+' FROM ('+sql.replace('%','%%')+') r'
  if number in (6,10):source+=' JOIN users u ON u.user_id=r.user_id'
  if ids.get('user_id') and number in (6,10):where('r.user_id=%s',ids['user_id'])
  if ids.get('profile_id') and number==8:where('r.profile_id=%s',ids['profile_id'])
  if ids.get('content_id') and number in (3,4,5):where('r.content_id=%s',ids['content_id'])
  if term and number in (3,4,5,9):where('r.title LIKE %s','%'+term+'%')
  if number==7 and ids.get('tier_id'):where('r.tier_id=%s',ids['tier_id'])
  if number==9:where('r.genre_name=(SELECT genre_name FROM genres WHERE genre_id=%s)',ids['genre_id'])
  if number==6 and values.get('auto_renew','')!='':where('r.auto_renew=%s',integer(values,'auto_renew',True,0,1))
  order={1:'r.date_released DESC,r.content_id DESC',2:'r.month_start',3:'r.rank_no,r.content_id',4:'r.content_id',5:'r.added_at DESC,r.content_id',6:'r.end_date,r.subscription_id',7:'r.revenue DESC,r.tier_id',8:'r.profile_id',9:'r.genre_name,r.rank_no,r.content_id',10:'r.user_id'}[number]
  return source,clauses,params,order,setups
 return source,clauses,params,order,{}

@app.get('/lab/search')
@login_required
def search():
 guard();values=request.args.to_dict();task=values.get('task','users')
 if task not in TASKS:abort(400)
 values['task']=task
 values.setdefault('date_from','1925-01-01' if task=='catalog' else '2025-01-01');values.setdefault('date_to','2021-12-31' if task=='catalog' else '2025-12-31');values.setdefault('top_n','3' if task=='genre_ranking' else '10');values.setdefault('days','30')
 c=db();rows=[];columns=[];count=0;error='';submitted=values.get('run')=='1';page_no=max(1,request.args.get('page',1,type=int))
 try:
  with c.cursor() as q:
   q.execute('SELECT user_id,full_name,email FROM users WHERE user_id=%s',(session['user_id'],));current=q.fetchone()
   q.execute('SELECT * FROM genres ORDER BY genre_name');genres=q.fetchall()
   q.execute('SELECT tier_id,tier_name FROM subscription_tiers ORDER BY tier_id');tiers=q.fetchall()
   if submitted:
    try:
     source,clauses,params,order,setups=build(values)
     for key,value in setups.items():q.execute('SET @'+key+'=%s',(value,))
     condition=(' WHERE '+' AND '.join(clauses)) if clauses else ''
     q.execute('SELECT COUNT(*) AS n FROM ('+source+condition+') results',params);count=q.fetchone()['n']
     page_no=min(page_no,max(1,(count+49)//50))
     q.execute(source+condition+' ORDER BY '+order+' LIMIT 50 OFFSET %s',params+[(page_no-1)*50]);rows=q.fetchall();columns=[d[0] for d in q.description]
    except ValueError as e:error=str(e)
 finally:c.close()
 previous=dict(values,page=max(1,page_no-1));following=dict(values,page=page_no+1)
 return render_template('management.html',tasks=TASKS,task=task,meta=TASKS[task],values=values,current=current,genres=genres,tiers=tiers,rows=rows,columns=columns,labels=LABELS,count=count,page_no=page_no,submitted=submitted,error=error,previous=previous,following=following)
