"""Chạy bốn script nguyên bản trên fixture, chặn chạy nhầm DB nguồn."""
import os,sys,subprocess,json
from pathlib import Path
import pymysql
if os.getenv('ALLOW_VERIFICATION_FIXTURES')!='1':raise SystemExit('Chạy bằng compose.verify.yaml, không dùng CSDL chính.')
r=Path(__file__).resolve().parents[1]
c=pymysql.connect(host=os.getenv('DB_HOST','db'),port=int(os.getenv('DB_PORT','3306')),user=os.getenv('DB_USER','root'),password=os.environ['DB_PASSWORD'],database='mini_netflix')
with c.cursor() as q:
 q.execute('SELECT (SELECT COUNT(*) FROM users),(SELECT COUNT(*) FROM profiles),(SELECT COUNT(*) FROM payments),(SELECT COUNT(*) FROM watch_histories)');counts=q.fetchone()
c.close()
if counts!=(100,200,100,25000):raise SystemExit('CSDL không phải fixture mới dự kiến, dừng: '+str(counts))
for name in ['verify.py','verify_demo.py','verify_semantics.py','verify_renewal.py']:subprocess.run([sys.executable,str(r/name)],cwd=r,check=True)
parts=['verification','demo_verification','semantic_verification','renewal_verification'];passed=total=0
for name in parts:
 rows=json.loads((r/'evidence'/(name+'.json')).read_text());total+=len(rows);passed+=sum(x['passed'] for x in rows)
print('ORIGINAL FIXTURE CHECKS',passed,'/',total)
if passed!=total:raise SystemExit(1)

fixture_dir=r/'evidence/fixture'
fixture_dir.mkdir(exist_ok=True)
for filename in ['verification.json','demo_verification.json','semantic_verification.json','renewal_verification.json','benchmark.json','explain_analyze.json','environment.json']:
 path=r/'evidence'/filename
 if path.exists():path.replace(fixture_dir/filename)
(fixture_dir/'summary.json').write_text(json.dumps(dict(passed=passed,total=total,scope='isolated synthetic verification fixtures; not sourced demo data'),ensure_ascii=False,indent=2))
