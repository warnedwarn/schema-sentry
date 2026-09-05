from conftest import CONTRACT
URLS=['https://old.example/openapi','https://new.example/openapi','https://policy.example/migration']
def mocks(v):
 v.strict_mocks=True;v.check_pickling=True;v.mock_web(r'old\.example',{'status':200,'body':'GET /users/{id}; required id'});v.mock_web(r'new\.example',{'status':200,'body':'GET /users/{id}; required id; optional locale'});v.mock_web(r'policy\.example',{'status':200,'body':'Optional additions are compatible.'});v.mock_llm(r'.*Compare old OpenAPI.*','{"verdict":"COMPATIBLE","breaking_paths":[],"covered_paths":[]}');v.mock_llm(r'.*Verify the exact verdict.*','{"valid":true}')
def test_lifecycle(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);mocks(direct_vm);c.register(' s-1 ','Profiles','v2',URLS);c.review('S-1');assert c.get_review('S-1')['verdict']=='COMPATIBLE';c.acknowledge('S-1');assert c.get_review('S-1')['state']=='ACKNOWLEDGED'
def test_ids_sources_replay(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);c.register('A','Profiles','v2',URLS)
 with direct_vm.expect_revert('duplicate review'):c.register(' a ','Profiles','v2',URLS)
 with direct_vm.expect_revert('independent source'):c.register('B','Profiles','v2',[URLS[0],URLS[0],URLS[2]])
def test_forged_digest_rejected(direct_vm,direct_deploy):
 c=direct_deploy(CONTRACT);mocks(direct_vm);c.register('X','Profiles','v2',URLS);x=c._compare(c.reviews['X']);assert direct_vm.run_validator(leader_result=x);x=dict(x);x['digests']=list(reversed(x['digests']));assert not direct_vm.run_validator(leader_result=x)
