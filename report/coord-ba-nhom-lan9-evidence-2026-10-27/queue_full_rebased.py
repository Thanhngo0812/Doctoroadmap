"""Wait for existing Python test runners without stopping them, then gate the pinned integration."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path('C:/Users/ngoco/Desktop/Doctoroadmap');HERE=Path(__file__).parent
EXPECTED='95827530da45194c353fd0bebffe6bbcb74b03ce'
WT=ROOT/'tmp/coord-r9-acceptance-20261027'
query="@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and $_.CommandLine -like '*w05_run_tests.py*' }).Count"
def save(status,**extra):(HERE/'queue-full-rebased.json').write_text(json.dumps(dict(status=status,**extra),indent=2)+'\n',encoding='utf-8')
started=time.monotonic()
while True:
    count=int(subprocess.check_output(['powershell','-NoProfile','-Command',query],text=True).strip() or '0')
    save('waiting_for_existing_test_runners',processes=count,waited_seconds=round(time.monotonic()-started,1))
    if count==0:break
    time.sleep(5)
head=subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
if head!=EXPECTED:
    save('main_changed_needs_coordinator_integration',observed_main=head,expected_main=EXPECTED)
    raise SystemExit(75)
save('running_full_gate',source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT,text=True).strip(),waited_seconds=round(time.monotonic()-started,1))
command=[str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'tmp/coord-review-20261021/run_check.py'),str(WT),str(HERE/'runs'),'full-rebased',str(ROOT/'.venv/Scripts/python.exe'),'scripts/w05_run_tests.py','-o','addopts=','-q','--basetemp=tmp/coord-r9-full-rebased','--junitxml='+str(HERE/'runs/full-rebased.xml')]
result=subprocess.run(command,cwd=ROOT)
save('finished',wrapper_exit_code=result.returncode)
raise SystemExit(result.returncode)
