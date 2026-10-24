import importlib.util,os
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r4-acceptance-20261024')
os.environ['W08_MUTATION_RUN']='mutations-coord-r4'
spec=importlib.util.spec_from_file_location('w08_mut',ROOT/'scripts/w08_mutations.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.CASES=tuple(c for c in module.CASES if c[0] in {'live-related-progress','self-check-heading-grammar'})
assert len(module.CASES)==2
module.main()
