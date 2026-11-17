"""Các giao dịch tài khoản bổ sung theo CT-01/02/04/06 của báo cáo."""
import re
from werkzeug.security import generate_password_hash
from app import db

def register(email,phone,full_name,password):
 if not re.fullmatch(r'[A-Za-z0-9._%+-]+@gmail\.com',email) or not re.fullmatch(r'[0-9]{10}',phone) or not full_name.strip() or not password:raise ValueError('Thông tin không hợp lệ')
 c=db()
 try:
  with c.cursor() as q:
   q.execute('INSERT INTO users(email,phone,full_name,password_hash) VALUES(%s,%s,%s,%s)',(email,phone,full_name,generate_password_hash(password)));uid=q.lastrowid
   q.execute("INSERT INTO profiles(user_id,profile_name) VALUES(%s,'Hồ sơ 1')",(uid,))
  c.commit();return uid
 except Exception:c.rollback();raise
 finally:c.close()

def subscribe(user_id,tier_id,method='E_WALLET'):
 """Tạo lượt mới sau khi lượt cũ kết thúc; không sửa tier_id của lượt cũ."""
 c=db()
 try:
  with c.cursor() as q:
   q.execute('SELECT user_id FROM users WHERE user_id=%s FOR UPDATE',(user_id,))
   if not q.fetchone():raise ValueError('Tài khoản không tồn tại')
   q.execute('SELECT COUNT(*) AS n FROM v_active_subscriptions WHERE user_id=%s',(user_id,))
   if q.fetchone()['n']:raise ValueError('Đang có gói hiệu lực')
   q.execute("SELECT subscription_id FROM subscriptions WHERE user_id=%s AND status='ACTIVE' AND start_date>CURRENT_TIMESTAMP",(user_id,))
   if q.fetchone():raise ValueError('Đã có gói đặt trước')
   q.execute('SELECT prices,max_profile FROM subscription_tiers WHERE tier_id=%s FOR SHARE',(tier_id,));tier=q.fetchone()
   if not tier:raise ValueError('Gói không tồn tại')
   q.execute('SELECT COUNT(*) AS n FROM profiles WHERE user_id=%s',(user_id,))
   if q.fetchone()['n']>tier['max_profile']:raise ValueError('Số hồ sơ vượt gói')
   q.execute("UPDATE subscriptions SET status='EXPIRED' WHERE user_id=%s AND status='ACTIVE' AND end_date<=CURRENT_TIMESTAMP",(user_id,))
   q.execute("INSERT INTO subscriptions(user_id,tier_id,start_date,end_date,status) VALUES(%s,%s,CURRENT_TIMESTAMP,DATE_ADD(CURRENT_TIMESTAMP,INTERVAL 30 DAY),'ACTIVE')",(user_id,tier_id));sid=q.lastrowid
   q.execute('INSERT INTO payments(subscription_id,prices,transaction_method) VALUES(%s,%s,%s)',(sid,tier['prices'],method))
  c.commit();return sid
 except Exception:c.rollback();raise
 finally:c.close()

def set_auto_renew(user_id,subscription_id,enabled):
 c=db()
 try:
  with c.cursor() as q:
   q.execute('SELECT user_id FROM users WHERE user_id=%s FOR UPDATE',(user_id,))
   if not q.fetchone():raise ValueError('Tài khoản không tồn tại')
   q.execute('UPDATE subscriptions SET auto_renew=%s WHERE subscription_id=%s AND user_id=%s',(bool(enabled),subscription_id,user_id))
  c.commit()
 except Exception:c.rollback();raise
 finally:c.close()
