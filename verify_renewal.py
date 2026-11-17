"""Sáu ca nhánh gia hạn và nguyên tử; cần DBA trên CSDL thử riêng."""
import json
from pathlib import Path
from datetime import datetime,timedelta,timezone
from verify import conn
ROOT=Path(__file__).resolve().parent
def main():
 c=conn();out=[]
 try:
  with c.cursor() as q:
   for idx,name,auto,is_auto,pay_ok,status,expired,expected,expected_error in [
    (999010,'Hết hạn, không tự gia hạn',0,1,1,'ACTIVE',True,'EXPIRED',None),
    (999011,'Tự gia hạn thất bại',1,1,0,'ACTIVE',True,'CANCELED',None),
    (999012,'Gia hạn thủ công thất bại',1,0,0,'ACTIVE',False,'ACTIVE',1644),
    (999013,'Chưa đến hạn không tự gia hạn',1,1,1,'ACTIVE',False,'ACTIVE',1644),
    (999014,'Lượt EXPIRED phải tạo đăng ký mới',1,0,1,'EXPIRED',True,'EXPIRED',1644),
    (999015,'Lỗi sau INSERT payment phải ROLLBACK toàn bộ',1,0,1,'ACTIVE',False,'ACTIVE',1644),
   ]:
    now=datetime.now(timezone.utc).replace(tzinfo=None,microsecond=0);start=now-timedelta(days=40 if expired else 10);end=now+timedelta(days=-10 if expired else 20)
    q.execute('INSERT INTO users(user_id,email,phone,password_hash,full_name) VALUES(%s,%s,%s,%s,%s)',(idx,f'verify{idx}@gmail.com',f'09{idx:08}','test-only','Kiểm thử gia hạn'))
    q.execute('INSERT INTO subscriptions(subscription_id,user_id,tier_id,start_date,end_date,auto_renew,status) VALUES(%s,%s,1,%s,%s,%s,%s)',(idx,idx,start,end,auto,status))
    if idx==999015:
     q.execute("""CREATE TRIGGER mn_verify_fail_update BEFORE UPDATE ON subscriptions
     FOR EACH ROW BEGIN IF NEW.subscription_id=999015 THEN
         SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Controlled failure for atomicity test';
     END IF; END""")
    error=None
    try:
     q.callproc('sp_renew_subscription',(idx,idx,end,is_auto,pay_ok,'CARD'))
     while q.nextset():pass
    except Exception as e:error=e.args[0]
    if idx==999015:q.execute('DROP TRIGGER mn_verify_fail_update')
    q.execute('SELECT status,end_date FROM subscriptions WHERE subscription_id=%s',(idx,));actual=q.fetchone()
    q.execute('SELECT COUNT(*) FROM payments WHERE subscription_id=%s',(idx,));payments=q.fetchone()[0]
    passed=actual==(expected,end) and payments==0 and error==expected_error
    out.append(dict(code='RENEW'+str(idx-999009),name=name,passed=passed,actual=f'status={actual[0]}; end_date không đổi={actual[1]==end}; payments={payments}; lỗi={error}'))
    q.execute('DELETE FROM subscriptions WHERE subscription_id=%s',(idx,));q.execute('DELETE FROM users WHERE user_id=%s',(idx,))
 finally:c.close()
 (ROOT/'evidence/renewal_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print('RENEWAL PASS',sum(x['passed'] for x in out),'/',len(out))
if __name__=='__main__':main()
