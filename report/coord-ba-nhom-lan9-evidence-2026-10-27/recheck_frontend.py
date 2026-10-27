import subprocess,sys
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap'); T=Path(__file__).parent; W=R/'tmp/coord-r9-acceptance-20261027'
wrapper=R/'tmp/coord-review-20261021/run_check.py'
commands=[('react-rebased',['npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit','--outputFile='+str(T/'runs/react-rebased.xml')]),('build-rebased',['npm.cmd','--prefix','src/web/frontend','run','build'])]
for label,args in commands:
    result=subprocess.run([sys.executable,str(wrapper),str(W),str(T/'runs'),label,*args],cwd=R)
    if result.returncode:raise SystemExit(result.returncode)
