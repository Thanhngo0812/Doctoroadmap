import os,subprocess,sys
from pathlib import Path
R=Path('C:/Users/ngoco/Desktop/Doctoroadmap'); T=Path(__file__).parent; W=R/'tmp/coord-r10-web-final-20261028'; wrapper=R/'tmp/coord-review-20261021/run_check.py'
commands=[('react-web-final',['npm.cmd','--prefix','src/web/frontend','test','--','--pool=threads','--maxWorkers=1','--reporter=default','--reporter=junit','--outputFile='+str(T/'runs/react-web-final.xml')]),('build-web-final',['npm.cmd','--prefix','src/web/frontend','run','build']),('browser-w04-web-final',[sys.executable,'scripts/w04_react_runtime.py'])]
for label,args in commands:
 env=dict(os.environ);env['W04_REACT_RUN']='browser-coord-r10-web-final'
 result=subprocess.run([sys.executable,str(wrapper),str(W),str(T/'runs'),label,*args],cwd=R,env=env)
 if result.returncode:raise SystemExit(result.returncode)
