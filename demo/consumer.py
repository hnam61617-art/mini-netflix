"""Giao diện người xem; dùng cùng 13 bảng và các endpoint ghi nghiệp vụ."""
from datetime import datetime,timezone,timedelta
from flask import request,session,render_template,abort,redirect,url_for,flash
import pymysql
from app import app,db,own,login_required,csrf

@app.template_filter('local_time')
def local_time(value):
    if not value:return '—'
    return (value+timedelta(hours=7)).strftime('%d/%m/%Y · %H:%M')

@app.template_filter('money')
def money(value):return f'{value:,.0f}'.replace(',','.')+' đ'

def context(q):
    q.execute('SELECT profile_id,profile_name FROM profiles WHERE user_id=%s ORDER BY profile_id',(session['user_id'],));profiles=q.fetchall()
    pid=request.args.get('profile_id',type=int) or session.get('active_profile') or (profiles[0]['profile_id'] if profiles else None)
    if pid:own(q,pid);session['active_profile']=pid
    q.execute('SELECT * FROM v_active_subscriptions WHERE user_id=%s',(session['user_id'],));subscription=q.fetchone()
    profile=next((p for p in profiles if p['profile_id']==pid),None)
    return dict(profiles=profiles,pid=pid,profile=profile,subscription=subscription)

def home():
    c=db()
    try:
        with c.cursor() as q:
            ctx=context(q);pid=ctx['pid'];keyword=request.args.get('q','').strip()[:255];kind=request.args.get('type','');genre=request.args.get('genre',type=int)
            view=request.args.get('view','home')
            if view not in ('home','list','history'):abort(400)
            q.execute('SELECT * FROM genres ORDER BY genre_name');genres=q.fetchall()
            sql='SELECT vc.* FROM v_content_catalog vc WHERE vc.title LIKE %s';params=['%'+keyword+'%']
            if kind in ('MOVIE','TV_SERIES'):sql+=' AND vc.content_type=%s';params.append(kind)
            if genre:sql+=' AND EXISTS (SELECT 1 FROM content_genres cg WHERE cg.content_id=vc.content_id AND cg.genre_id=%s)';params.append(genre)
            if view=='list':
                sql+=' AND EXISTS(SELECT 1 FROM watch_lists chosen WHERE chosen.content_id=vc.content_id AND chosen.profile_id=%s)';params.append(pid or 0)
            q.execute(sql.replace('SELECT vc.* FROM v_content_catalog vc','SELECT COUNT(*) AS n FROM contents vc',1),params);catalog_count=q.fetchone()['n']
            page_no=min(max(1,request.args.get('page',1,type=int)),max(1,(catalog_count+47)//48))
            sql+=' ORDER BY vc.content_id LIMIT 48 OFFSET %s';q.execute(sql,params+[(page_no-1)*48]);contents=q.fetchall()
            watchlist=[];histories=[]
            if pid:
                q.execute('SELECT vc.* FROM watch_lists wl JOIN v_content_catalog vc ON vc.content_id=wl.content_id WHERE wl.profile_id=%s ORDER BY wl.added_at DESC,wl.content_id',(pid,));watchlist=q.fetchall()
                q.execute('''SELECT wh.history_id,COALESCE(wh.content_id,e.content_id) AS content_id,
                    wh.episode_id,e.episode_number,vc.title,vc.content_type,vc.genre_names,
                    wh.watch_progress,wh.last_watch_at,(wh.watch_progress>=90) AS completed_status
                    FROM watch_histories wh LEFT JOIN episodes e ON e.episode_id=wh.episode_id
                    JOIN v_content_catalog vc ON vc.content_id=COALESCE(wh.content_id,e.content_id)
                    WHERE wh.profile_id=%s ORDER BY wh.last_watch_at DESC,wh.history_id DESC LIMIT 100''',(pid,));histories=q.fetchall()
    finally:c.close()
    saved={w['content_id'] for w in watchlist};continuing=[h for h in histories if 0<h['watch_progress']<90]
    return render_template('consumer/home.html',**ctx,contents=contents,keyword=keyword,kind=kind,genre=genre,genres=genres,view=view,saved=saved,histories=histories,continuing=continuing,featured=contents[0] if contents else None,catalog_count=catalog_count,page_no=page_no,previous=dict(request.args.to_dict(),page=max(1,page_no-1)),following=dict(request.args.to_dict(),page=page_no+1))

@app.get('/content/<int:cid>')
@login_required
def content_detail(cid):
    c=db()
    try:
        with c.cursor() as q:
            ctx=context(q);pid=ctx['pid']
            q.execute('SELECT vc.*,c.description FROM v_content_catalog vc JOIN contents c ON c.content_id=vc.content_id WHERE vc.content_id=%s',(cid,));content=q.fetchone()
            if not content:abort(404)
            q.execute('SELECT episode_id,episode_number,title,duration,date_released FROM episodes WHERE content_id=%s ORDER BY episode_number',(cid,));episodes=q.fetchall()
            selected=None
            if content['content_type']=='TV_SERIES' and episodes:
                eid=request.args.get('episode_id',type=int)
                selected=next((e for e in episodes if e['episode_id']==eid),None) if eid else episodes[0]
                if not selected:abort(404)
            saved=False;history=None;episode_progress={}
            if pid:
                q.execute('SELECT content_id FROM watch_lists WHERE profile_id=%s AND content_id=%s',(pid,cid));saved=bool(q.fetchone())
                if content['content_type']=='MOVIE':q.execute('SELECT watch_progress FROM watch_histories WHERE profile_id=%s AND content_id=%s',(pid,cid));history=q.fetchone()
                elif selected:q.execute('SELECT watch_progress FROM watch_histories WHERE profile_id=%s AND episode_id=%s',(pid,selected['episode_id']));history=q.fetchone()
                if episodes:
                    q.execute('SELECT wh.episode_id,wh.watch_progress FROM watch_histories wh JOIN episodes e ON e.episode_id=wh.episode_id WHERE wh.profile_id=%s AND e.content_id=%s',(pid,cid));episode_progress={r['episode_id']:r['watch_progress'] for r in q.fetchall()}
    finally:c.close()
    target='movie:'+str(cid) if content['content_type']=='MOVIE' else ('episode:'+str(selected['episode_id']) if selected else None)
    return render_template('consumer/detail.html',**ctx,content=content,episodes=episodes,selected=selected,saved=saved,progress=history['watch_progress'] if history else 0,target=target,episode_progress=episode_progress,view='detail')

@app.get('/account')
@login_required
def account():
    c=db()
    try:
        with c.cursor() as q:
            ctx=context(q)
            q.execute('SELECT full_name,email FROM users WHERE user_id=%s',(session['user_id'],));user=q.fetchone()
            q.execute('SELECT * FROM subscription_tiers ORDER BY prices');tiers=q.fetchall()
            q.execute('''SELECT p.prices,p.transaction_method,p.history_payment FROM payments p
                JOIN subscriptions s ON s.subscription_id=p.subscription_id WHERE s.user_id=%s
                ORDER BY p.history_payment DESC,p.payment_id DESC LIMIT 10''',(session['user_id'],));payments=q.fetchall()
    finally:c.close()
    return render_template('consumer/account.html',**ctx,user=user,tiers=tiers,payments=payments,view='account')

@app.route('/register',methods=['GET','POST'])
def register():
    error=''
    if request.method=='POST':
        from accounts import register as create_account
        try:
            uid=create_account(request.form.get('email','').strip(),request.form.get('phone','').strip(),request.form.get('full_name','').strip(),request.form.get('password',''))
        except ValueError:error='Kiểm tra email @gmail.com, số điện thoại 10 chữ số, họ tên và mật khẩu.'
        except pymysql.IntegrityError:error='Email hoặc số điện thoại đã được sử dụng, hoặc thông tin chưa hợp lệ.'
        else:
            session.clear();session['user_id']=uid;csrf();flash('Tài khoản đã được tạo. Chọn gói dịch vụ để bắt đầu xem.');return redirect(url_for('account'))
    return render_template('consumer/auth.html',register=True,error=error)

@app.post('/subscribe')
@login_required
def subscribe():
    from accounts import subscribe as create_subscription
    tier=request.form.get('tier_id',type=int)
    if not tier:abort(400)
    try:create_subscription(session['user_id'],tier)
    except ValueError as e:flash(str(e))
    else:flash('Đã đăng ký gói 30 ngày và ghi nhận thanh toán mô phỏng.')
    return redirect(url_for('account'))

@app.post('/auto-renew')
@login_required
def auto_renew():
    from accounts import set_auto_renew
    sid=request.form.get('subscription_id',type=int)
    if not sid:abort(400)
    set_auto_renew(session['user_id'],sid,request.form.get('enabled')=='1');flash('Đã cập nhật tự động gia hạn.');return redirect(url_for('account'))

@app.get('/data-sources')
def data_sources():
    return render_template('data_sources.html')
