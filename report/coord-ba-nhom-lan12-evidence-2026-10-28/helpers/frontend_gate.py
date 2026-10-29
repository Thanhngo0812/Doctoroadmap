import subprocess,sys
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-acceptance-20261028');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-tools-20261028')
for label,args in [('react-final',['npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit','--outputFile='+str(T/'runs/react-final.xml')]),('build-final',['npm.cmd','--prefix','src/web/frontend','run','build'])]:
 r=subprocess.run([sys.executable,str(R/'tmp/coord-review-20261021/run_check.py'),str(W),str(T/'runs'),label,*args],cwd=R)
 if r.returncode:raise SystemExit(r.returncode)
