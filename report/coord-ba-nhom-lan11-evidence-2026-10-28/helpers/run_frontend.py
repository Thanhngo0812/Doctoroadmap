import os,subprocess,sys
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap');T=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028');W=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-final-20261028');wrapper=R/'tmp/coord-review-20261021/run_check.py'
commands=[('react-final',['npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit','--outputFile='+str(T/'runs/react-final.xml')]),('build-final',['npm.cmd','--prefix','src/web/frontend','run','build']),('browser-w12',[sys.executable,'scripts/w12_react_runtime.py'])]
for label,args in commands:
 env=dict(os.environ,W12_REACT_RUN='browser-coord-r11-final');r=subprocess.run([sys.executable,str(wrapper),str(W),str(T/'runs'),label,*args],cwd=R,env=env)
 if r.returncode:raise SystemExit(r.returncode)
