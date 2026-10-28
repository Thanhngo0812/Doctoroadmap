from test_w17_admin import admin_case, patch, sql
import json
from pathlib import Path

def test_disabled_later_admin_can_be_demoted_without_removing_active_admin(admin_case):
    rt=admin_case
    later=rt.user(True)
    assert patch(rt,{'status':'disabled'},target=later).status_code==200
    assert rt.services.admin.store.admin_count()==1
    response=patch(rt,{'role':'user','build_monthly_max':7},target=later)
    proof={'response_status':response.status_code,'response':response.json(),'accounts':sql(rt,'SELECT id,role,status,build_monthly_max FROM account WHERE id IN (:a,:b)',a=rt.owner.id,b=later.id),'first_admin_id':rt.services.admin.store.first_admin_id(),'owner_id':rt.owner.id,'later_id':later.id}
    Path(r'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r11-tools-20261028/core-probe-proof.json').write_text(json.dumps(proof,indent=2,default=str))
    assert response.status_code==200, response.text
    assert sql(rt,'SELECT role,status,build_monthly_max FROM account WHERE id=:id',id=later.id)==[{'role':'user','status':'disabled','build_monthly_max':7}]
    assert rt.owner.client.get('/api/v1/me').status_code==200
