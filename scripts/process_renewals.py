"""Worker mô phỏng: python scripts/process_renewals.py [--payment-fails]."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'demo'))
from app import db
c=db()
try:
 with c.cursor() as q:q.execute("SELECT user_id,subscription_id,end_date FROM subscriptions WHERE status='ACTIVE' AND end_date<=CURRENT_TIMESTAMP ORDER BY subscription_id");rows=q.fetchall()
finally:c.close()
for row in rows:
 c=db()
 try:
  with c.cursor() as q:
   q.callproc('sp_renew_subscription',(row['user_id'],row['subscription_id'],row['end_date'],True,'--payment-fails' not in sys.argv,'E_WALLET'))
   while q.nextset():pass
  print(row['subscription_id'],'OK')
 except Exception as e:print(row['subscription_id'],'SKIPPED',type(e).__name__)
 finally:c.close()
