import hashlib
from conftest import CONTRACT

URLS=['https://old.example/openapi','https://new.example/openapi','https://policy.example/migration']
BODIES=['OpenAPI v1: GET /users/{id}; required id','OpenAPI v2: GET /users/{id}; required id; optional locale','Migration policy: optional additions are compatible.']
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def freeze(v):
 v.strict_mocks=True;v.check_pickling=True
 for host,body in zip(('old','new','policy'),BODIES):v.mock_web(host+r'\.example',{'status':200,'body':body})
def registered(v,deploy,alice,bob,charlie):
 freeze(v);contract=deploy(CONTRACT);authorities=['0x'+bob.hex(),'0x'+charlie.hex(),'0x'+bytes.fromhex('11'*20).hex()];controller='0x'+charlie.hex()
 contract.register('S-1','Profiles API','v2',URLS,authorities,controller);return contract,authorities

def test_registration_freezes_full_digests(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 contract,_=registered(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie);state=contract.get_review('S-1')
 assert state['state']=='PENDING_ATTESTATIONS' and state['digests']==[digest(body) for body in BODIES]

def test_each_distinct_authority_must_attest_exact_digest(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 contract,authorities=registered(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie);digests=contract.get_review('S-1')['digests']
 direct_vm.sender=direct_bob
 with direct_vm.expect_revert('matching source authority'):contract.attest_source('S-1',0,'0'*64)
 contract.attest_source('S-1',0,digests[0]);direct_vm.sender=direct_charlie;contract.attest_source('S-1',1,digests[1]);direct_vm.sender=bytes.fromhex('11'*20);contract.attest_source('S-1',2,digests[2])
 assert contract.get_review('S-1')['state']=='READY'

def test_compatible_verdict_gates_release_controller_right(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 contract,_=registered(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie);digests=contract.get_review('S-1')['digests']
 for sender,slot in ((direct_bob,0),(direct_charlie,1),(bytes.fromhex('11'*20),2)):direct_vm.sender=sender;contract.attest_source('S-1',slot,digests[slot])
 direct_vm.mock_llm(r'.*SchemaSentry.*','{"verdict":"COMPATIBLE","breaking_paths":[],"covered_paths":["/users/{id}"]}')
 direct_vm.mock_llm(r'.*SchemaSentry.*','{"verdict":"COMPATIBLE","breaking_paths":[],"covered_paths":["/users/{id}"]}')
 contract.review('S-1');direct_vm.sender=direct_alice
 with direct_vm.expect_revert('approved release controller'):contract.execute_release('S-1')
 direct_vm.sender=direct_charlie;contract.execute_release('S-1');assert contract.get_review('S-1')['state']=='RELEASED'

def test_blocked_verdict_cannot_release(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 contract,_=registered(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie);digests=contract.get_review('S-1')['digests']
 for sender,slot in ((direct_bob,0),(direct_charlie,1),(bytes.fromhex('11'*20),2)):direct_vm.sender=sender;contract.attest_source('S-1',slot,digests[slot])
 for _ in range(2):direct_vm.mock_llm(r'.*SchemaSentry.*','{"verdict":"BLOCKED","breaking_paths":["/users/{id}"],"covered_paths":[]}')
 contract.review('S-1');direct_vm.sender=direct_charlie
 with direct_vm.expect_revert('approved release controller'):contract.execute_release('S-1')

def test_owner_cannot_control_authority_slots(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 freeze(direct_vm);contract=direct_deploy(CONTRACT);direct_vm.sender=direct_alice
 with direct_vm.expect_revert('independent source authorities'):
  contract.register('BAD','Profiles API','v2',URLS,['0x'+direct_alice.hex(),'0x'+direct_bob.hex(),'0x'+direct_charlie.hex()],'0x'+direct_bob.hex())

def test_duplicate_ids_and_hosts_rejected(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 contract,authorities=registered(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie)
 with direct_vm.expect_revert('duplicate review'):contract.register(' s-1 ','Profiles API','v2',URLS,authorities,'0x'+direct_charlie.hex())
 with direct_vm.expect_revert('independent source hosts'):contract.register('S-2','Profiles API','v2',[URLS[0],URLS[0],URLS[2]],authorities,'0x'+direct_charlie.hex())

def test_forged_validator_fields_are_rejected(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie):
 contract,_=registered(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie);review=contract.reviews['S-1']
 for _ in range(2):direct_vm.mock_llm(r'.*SchemaSentry.*','{"verdict":"COMPATIBLE","breaking_paths":[],"covered_paths":["/users/{id}"]}')
 result=contract._compare(review);assert direct_vm.run_validator(leader_result=result);forged=dict(result);forged['covered']=[];assert not direct_vm.run_validator(leader_result=forged)
