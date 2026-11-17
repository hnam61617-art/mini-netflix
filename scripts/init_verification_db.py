"""Chỉ dựng fixture trong MySQL thử riêng, không sửa CSDL nguồn đang có."""
import os,sys
from pathlib import Path
import pymysql
from init_db import statements
if os.getenv('ALLOW_VERIFICATION_FIXTURES')!='1':raise SystemExit('Dùng compose.verify.yaml cho fixture, không nạp vào CSDL chính.')
r=Path(__file__).resolve().parents[1]
c=pymysql.connect(host=os.getenv('DB_HOST','db'),port=int(os.getenv('DB_PORT','3306')),user='root',password=os.environ['DB_PASSWORD'],charset='utf8mb4',autocommit=False)
try:
 with c.cursor() as q:
  q.execute("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='mini_netflix'")
  if q.fetchone()[0]:raise RuntimeError('DB thử đã tồn tại. Không tự xóa hoặc ghi đè.')
  for path in [r/'sql/01_schema.sql',r/'datasets/fixtures/verification_seed.sql',r/'sql/04_roles.sql',r/'sql/05_demo_accounts.sql']:
   for line,sql in statements(path.read_text(encoding='utf-8-sig')):q.execute(sql)
   c.commit()
 print('VERIFICATION FIXTURE READY — synthetic data in isolated test database')
finally:c.close()
