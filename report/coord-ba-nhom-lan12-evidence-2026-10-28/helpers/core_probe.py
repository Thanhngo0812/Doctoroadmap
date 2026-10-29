import json
from pathlib import Path
import pytest
from test_w17_admin import admin_case,patch,sql

@pytest.mark.parametrize('enable',[False,True])
def test_independent_disabled_admin_demotion_keeps_bootstrap_live(admin_case,enable):
 rt=admin_case;b=rt.user(True)
 assert patch(rt,{'status':'disabled'},target=b).status_code==200
 data={'role':'user','build_monthly_max':7}
 if enable:data['status']='active'
 response=patch(rt,data,target=b)
 proof={'response_status':response.status_code,'response':response.json(),'accounts':sql(rt,'SELECT id,role,status,build_monthly_max FROM account WHERE id IN (:a,:b)',a=rt.owner.id,b=b.id),'registry':sql(rt,'SELECT account_id FROM bootstrap_admin'),'bootstrap_id':rt.owner.id,'later_id':b.id}
 Path(r'C:/Users/ngoco/Desktop/Doctoroadmap/tmp/coord-r12-tools-20261028/core-probe-enable-'+str(enable)+'.json').write_text(json.dumps(proof,indent=2,default=str))
 assert response.status_code==200,response.text
 assert sql(rt,'SELECT role,status,build_monthly_max FROM account WHERE id=:id',id=b.id)==[{'role':'user','status':'active' if enable else 'disabled','build_monthly_max':7}]
 assert str(proof['registry'][0]['account_id'])==rt.owner.id
 assert rt.owner.client.get('/api/v1/me').status_code==200
 assert b.client.get('/api/v1/me').status_code==401
