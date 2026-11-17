"""Nạp SQL qua PyMySQL: gửi cả khối trigger/procedure, không dùng parser mysql CLI.
Chỉ khởi tạo CSDL chưa tồn tại; không tự xóa hoặc sửa CSDL nạp dở.
"""
import os,re,time,json,sys
from pathlib import Path
import pymysql
ROOT=Path(__file__).resolve().parents[1]
FILES=['01_schema.sql','02_seed.sql','04_roles.sql','05_demo_accounts.sql']

def statements(source):
    delimiter=';';buf=[]
    for number,line in enumerate(source.splitlines(),1):
        stripped=line.strip()
        if not stripped or stripped.startswith('--'):continue
        if stripped.upper().startswith('DELIMITER '):
            if buf:raise ValueError(f'DELIMITER giữa câu SQL ở dòng {number}')
            delimiter=stripped.split(None,1)[1];continue
        buf.append(line)
        if stripped.endswith(delimiter):
            text='\n'.join(buf).rstrip()[:-len(delimiter)].strip();buf=[]
            if text:yield number,text
    if buf:raise ValueError('Câu SQL cuối thiếu dấu kết thúc')

def verify(q):
    q.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='mini_netflix' AND table_type='BASE TABLE'");tables=q.fetchone()[0]
    q.execute("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema='mini_netflix'");triggers=q.fetchone()[0]
    q.execute("SELECT COUNT(*) FROM information_schema.views WHERE table_schema='mini_netflix'");views=q.fetchone()[0]
    q.execute("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='mini_netflix' AND routine_type='PROCEDURE'");procedures=q.fetchone()[0]
    q.execute('SELECT COUNT(*) FROM mini_netflix.watch_histories');histories=q.fetchone()[0]
    q.execute('SELECT COUNT(*) FROM mini_netflix.contents');contents=q.fetchone()[0]
    q.execute("SELECT COUNT(*) FROM mysql.user WHERE user IN ('mn_service','mn_presenter','mn_editor') AND host='%'");accounts=q.fetchone()[0]
    actual=dict(tables=tables,triggers=triggers,views=views,procedures=procedures,histories=histories,accounts=accounts,contents=contents)
    if (tables,triggers,views,procedures,accounts)!=(13,13,4,1,3) or contents<8807:raise RuntimeError('CSDL chưa hoàn tất: '+json.dumps(actual))
    print('INIT VERIFIED',json.dumps(actual),flush=True)

def main():
    plans=[(name,list(statements((ROOT/'sql'/name).read_text(encoding='utf-8-sig')))) for name in FILES]
    if '--check-sql' in sys.argv:
        for name,items in plans:print(name,len(items),'statements')
        return
    c=None
    for attempt in range(60):
        try:
            c=pymysql.connect(host=os.getenv('DB_HOST','127.0.0.1'),port=int(os.getenv('DB_PORT','3306')),user=os.getenv('DB_USER','root'),password=os.environ['DB_PASSWORD'],charset='utf8mb4',autocommit=False,connect_timeout=5)
            break
        except pymysql.OperationalError:
            if attempt==59:raise
            time.sleep(2)
    try:
        with c.cursor() as q:
            q.execute("SET SESSION time_zone='+00:00'")
            q.execute("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='mini_netflix'")
            if q.fetchone()[0]:
                verify(q);print('Existing sourced database preserved.',flush=True);return
            for name,items in plans:
                print('INIT',name,flush=True)
                for line,sql in items:
                    try:q.execute(sql)
                    except Exception:
                        c.rollback();print(f'INIT FAILED: {name}, statement ending at line {line}',flush=True);raise
                c.commit()
            verify(q)
    finally:c.close()
if __name__=='__main__':main()
