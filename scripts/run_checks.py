"""Mặc định: kiểm chứng nguồn chính. Fixture gốc chạy trong compose.verify.yaml."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if '--fixtures' in sys.argv:
 subprocess.run([sys.executable,str(root/'scripts/run_original_checks.py')],cwd=root,check=True)
else:
 subprocess.run([sys.executable,str(root/'verify_sourced.py')]+(['--fresh'] if '--fresh' in sys.argv else []),cwd=root,check=True)
 subprocess.run([sys.executable,str(root/'scripts/benchmark_sourced.py')],cwd=root,check=True)
