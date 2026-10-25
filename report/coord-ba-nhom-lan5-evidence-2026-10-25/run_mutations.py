import importlib.util,os
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r5-acceptance-20261025')
os.environ['W09_MUTATION_RUN']='mutations-coord-r5'
spec=importlib.util.spec_from_file_location('w09_mutations',ROOT/'scripts/w09_mutation_checks.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
selected={'ui-retry-id','ui-fabricated-link'}
module.cases=[case for case in module.cases if case[0] in selected]
assert len(module.cases)==2
raise SystemExit(module.main())
