from pathlib import Path
import ast,json,re,os,importlib.util
project=Path.cwd(); source=project/'tmp/w24-figma-evidence'; evidence=project/'tmp/coord-w24-review-20261022'
raw_path=evidence/'design/tokens/figma_variables_raw_export.json'; original=raw_path.read_text(encoding='utf-8');raw=json.loads(original)
spec=importlib.util.spec_from_file_location('token_source',source/'scripts/verify_wcag_contrast.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
light,dark=helper.parse_css_tokens((source/'design/tokens/tokens.css').read_text(encoding='utf-8'));effective={'Light':light,'Dark':dict(light,**dark)}
comparisons=[]
for v in raw['variables']:
 for mode in ['Light','Dark']:
  value=v['valuesByMode'][mode]; expected=str(value)+'px' if v['type']=='FLOAT' else str(value);actual=effective[mode].get(v['cssProperty'])
  comparisons.append({'name':v['name'],'mode':mode,'cssProperty':v['cssProperty'],'rawValue':value,'cssValue':actual,'matches':actual is not None and helper.normalize_val(actual)==helper.normalize_val(expected)})
module=ast.parse((source/'tests/unit/presentation/test_tokens_and_wcag.py').read_text(encoding='utf-8'));fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='test_figma_variables_raw_export_valid');namespace={'json':json,'Path':Path};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source/'tests/unit/presentation/test_tokens_and_wcag.py'),'exec'),namespace)
mutations=[('baseline',None,None,None),('primary-light-changed','color/primary','Light','#FF0000'),('brand-tint-dark-changed','color/brand-tint','Dark','rgba(41, 169, 255, 0.99)'),('spacing4-dark-changed','spacing/space-4','Dark',999),('radius-lg-dark-changed','radius/radius-lg','Dark',999),('motion-base-light-changed','motion/motion-base','Light','999ms')];results=[]
try:
 os.chdir(evidence)
 for label,name,mode,value in mutations:
  data=json.loads(original)
  if name:next(v for v in data['variables'] if v['name']==name)['valuesByMode'][mode]=value
  raw_path.write_text(json.dumps(data),encoding='utf-8')
  try:namespace['test_figma_variables_raw_export_valid']();passed=True
  except AssertionError:passed=False
  results.append({'label':label,'guardPassed':passed})
finally:os.chdir(project);raw_path.write_text(original,encoding='utf-8')
old=json.loads((source/'report/w24-evidence/figma_variables_raw_export.json').read_text(encoding='utf-8'))
result={'sourceHead':'f1ca86dccdf5f7b8e224d325314324050fe415f1','workerNeverModified':True,'scratchRawRestored':True,'comparisons':comparisons,'comparisonCount':len(comparisons),'mismatchCount':sum(not c['matches'] for c in comparisons),'rawGuardCounterexamples':results,'reportEvidenceRawCount':len(old['variables']),'designRawCount':len(raw['variables']),'reportEvidenceMetadata':old['metadata']}
(evidence/'token-css-observations.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print('mode comparisons',len(comparisons),'mismatches',result['mismatchCount']);print(json.dumps(results))
