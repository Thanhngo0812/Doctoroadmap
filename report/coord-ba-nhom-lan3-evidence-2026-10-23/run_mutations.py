import importlib.util, os
from pathlib import Path
root=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r3-acceptance-20261023')
os.environ['W08_MUTATION_RUN']='mutations-coord-r3'
spec=importlib.util.spec_from_file_location('w08_mutations',root/'scripts/w08_mutations.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.CASES=tuple(c for c in module.CASES if c[0] in {'cache-only','http-dto-privacy','safe-math'})
assert len(module.CASES)==3
module.main()
