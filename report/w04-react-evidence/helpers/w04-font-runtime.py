import sys,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
os.environ['W04_REACT_RUN']='browser-font-proof'
import w04_react_runtime as runtime
original=runtime.subprocess.run
def run(args,*a,**kw):
 if args[0]=='node':args=['node',str(Path.cwd()/'tmp/w04-font.cjs')]
 return original(args,*a,**kw)
runtime.subprocess.run=run
raise SystemExit(runtime.main())
